import pytest

from web.domains.case._import.sanctions.forms import (
    EditSanctionsAndAdhocLicenceForm,
    GoodsForm,
    SubmitSanctionsAndAdhocLicenceForm,
)
from web.models import Commodity, Country, Task
from web.tests.auth import AuthTestCase
from web.tests.domains.case._import.factory import (
    SanctionsAndAdhocLicenseApplicationFactory,
)


class TestSanctionsAndAdhocImportAppplicationForm(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.valid_country = Country.util.get_all_countries().get(name="Iran")

        self.process = SanctionsAndAdhocLicenseApplicationFactory.create(
            status="IN_PROGRESS",
            importer=self.importer,
            created_by=self.importer_user,
            last_updated_by=self.importer_user,
            origin_country=Country.objects.get(name="Iran"),
        )
        Task.objects.create(process=self.process, task_type=Task.TaskType.PREPARE)

    def test_sa_form_valid(self):
        data = {
            "contact": self.importer_user.pk,
            "origin_country": self.valid_country.pk,
            "consignment_country": self.valid_country.pk,
            "exporter_name": None,
            "exporter_address": None,
        }
        form = SubmitSanctionsAndAdhocLicenceForm(
            data, instance=self.process, initial={"contact": self.importer_user}
        )
        assert form.is_valid(), form.errors

    def test_sa_form_invalid_without_required_fields(self):
        data = {"exporter_name": None, "exporter_address": None}
        form = SubmitSanctionsAndAdhocLicenceForm(
            data, instance=self.process, initial={"contact": self.importer_user}
        )
        assert form.is_valid() is False
        assert form.errors
        assert len(form.errors) == 3

    def test_goods_form_valid(self):
        data = {
            "commodity": Commodity.objects.get(commodity_code="2709009000").pk,
            "goods_description": "test desc",
            "quantity_amount": 5,
            "value": 5,
        }
        form = GoodsForm(data, application=self.process)
        assert form.is_valid() is True

    def test_goods_form_invalid(self):
        data = {}
        form = GoodsForm(data, application=self.process)
        assert form.is_valid() is False
        assert len(form.errors) == 4

    def test_sanctioned_country_selected(self):
        sanctioned_countries = Country.app.get_sanctions_countries()
        invalid_countries = Country.util.get_all_countries().exclude(
            pk__in=sanctioned_countries.values_list("pk")
        )

        # Test both invalid
        form = EditSanctionsAndAdhocLicenceForm(
            data={
                "origin_country": invalid_countries[0],
                "consignment_country": invalid_countries[1],
            },
            instance=self.process,
        )
        assert not form.is_valid()
        assert form.errors["origin_country"][0] == (
            "The country of manufacture or country of shipment must be one of Belarus, Iran,"
            " Korea (North), Libya, Russian Federation, Somalia or Syria"
        )

        # Test sanctioned origin_country is valid
        form = EditSanctionsAndAdhocLicenceForm(
            data={
                "origin_country": sanctioned_countries[0],
                "consignment_country": invalid_countries[0],
            },
            instance=self.process,
        )
        assert form.is_valid()

        # Test sanctioned consignment_country is valid.
        form = EditSanctionsAndAdhocLicenceForm(
            data={
                "origin_country": invalid_countries[0],
                "consignment_country": sanctioned_countries[0],
            },
            instance=self.process,
        )
        assert form.is_valid()

    def test_sanctions_goods_filter(self):
        #
        # No countries selected == no commodities available.
        self.process.origin_country = None
        self.process.consignment_country = None
        self.process.save()

        form = GoodsForm(application=self.process)
        assert not form.fields["commodity"].queryset.exists()

        #
        # Setting origin country to sanctioned country == commodities available
        self.process.origin_country = Country.app.get_sanctions_countries().get(name="Iran")
        self.process.consignment_country = None
        self.process.save()

        form = GoodsForm(application=self.process)
        assert form.fields["commodity"].queryset.exists()

        #
        # Setting consignment country to sanctioned country == commodities available
        self.process.origin_country = None
        self.process.consignment_country = Country.app.get_sanctions_countries().get(name="Syria")
        self.process.save()

        form = GoodsForm(application=self.process)
        assert form.fields["commodity"].queryset.exists()
