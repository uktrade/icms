import pytest

from web.domains.case._import.sanctions.forms import (
    EditSanctionsAndAdhocLicenceForm,
    GoodsForm,
    GoodsSanctionsLicenceForm,
    SubmitSanctionsAndAdhocLicenceForm,
)
from web.models import Commodity, Country
from web.tests.auth import AuthTestCase


class TestSanctionsAndAdhocImportAppplicationForm(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, sanctions_app_in_progress):
        self.valid_country = Country.util.get_all_countries().get(name="Iran")
        self.process = sanctions_app_in_progress
        self.goods = self.process.sanctions_goods.first()

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
            "commodity": Commodity.objects.get(commodity_code="9013109000").pk,
            "goods_description": "test desc",
            "quantity_amount": 5,
            "value": 5,
        }
        form = GoodsForm(data, application=self.process)
        assert form.is_valid() is True
        assert form.cleaned_data["goods_description"] == "test desc"

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
        self.process.origin_country = Country.app.get_sanctions_countries().get(name="Belarus")
        self.process.consignment_country = None
        self.process.save()

        form = GoodsForm(application=self.process)
        assert form.fields["commodity"].queryset.exists()

        #
        # Setting consignment country to sanctioned country == commodities available
        self.process.origin_country = None
        self.process.consignment_country = Country.app.get_sanctions_countries().get(
            name="Russian Federation"
        )
        self.process.save()

        form = GoodsForm(application=self.process)
        assert form.fields["commodity"].queryset.exists()

    def test_goods_form_description_cleaned(self):
        data = {
            "commodity": Commodity.objects.get(commodity_code="9013109000").pk,
            "goods_description": " some\r\n goods \t description\n  ",
            "quantity_amount": 5,
            "value": 5,
        }
        form = GoodsForm(data, application=self.process)
        assert form.is_valid() is True
        assert form.cleaned_data["goods_description"] == "some goods description"

    def test_goods_sanction_licence_form(self):
        data = {
            "goods_description": "some goods description",
            "quantity_amount": 5,
            "value": 5,
        }
        form = GoodsSanctionsLicenceForm(data=data, instance=self.goods)
        assert form.is_valid() is True
        assert form.cleaned_data["goods_description"] == "some goods description"

    def test_goods_sanction_licence_form_description_cleaned(self):
        data = {
            "goods_description": " some\r\n goods \t description\n  ",
            "quantity_amount": 5,
            "value": 5,
        }
        form = GoodsSanctionsLicenceForm(data=data, instance=self.goods)
        assert form.is_valid() is True
        assert form.cleaned_data["goods_description"] == "some goods description"
