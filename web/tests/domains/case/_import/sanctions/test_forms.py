import pytest

from web.domains.case._import.sanctions.forms import (
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
        Country.objects.filter(country_groups__name="Sanctions and Adhoc License")

        self.valid_country = Country.objects.filter(
            country_groups__name="Sanctions and Adhoc License"
        ).first()
        self.invalid_country = Country.objects.exclude(
            country_groups__name="Sanctions and Adhoc License"
        ).first()

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

    def test_sa_form_invalid_with_wrong_country(self):
        data = {
            "contact": self.importer_user.pk,
            "origin_country": self.invalid_country.pk,
            "consignment_country": self.invalid_country.pk,
            "exporter_name": None,
            "exporter_address": None,
        }
        form = SubmitSanctionsAndAdhocLicenceForm(
            data, instance=self.process, initial={"contact": self.importer_user}
        )
        assert form.is_valid() is False
        assert form.errors

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
