import pytest
from django.utils import timezone

from web.domains.case._import.derogations.forms import SubmitDerogationsForm
from web.models import Commodity, Country
from web.tests.domains.case._import.factory import DerogationsApplicationFactory


class TestDerogationsForm:
    @pytest.fixture(autouse=True)
    def _setup(self, importer_one_contact, importer):
        self.user = importer_one_contact
        self.importer = importer

        self.valid_country = Country.objects.filter(
            country_groups__name="Derogation from Sanctions COOs"
        ).first()
        self.invalid_country = Country.objects.exclude(
            country_groups__name="Derogation from Sanctions COOs"
        ).first()

        self.process = DerogationsApplicationFactory.create(
            status="IN_PROGRESS",
            importer=self.importer,
            created_by=self.user,
            last_updated_by=self.user,
        )

    def test_da_form_valid(self):
        data = {
            "contact": self.user.pk,
            "origin_country": self.valid_country.pk,
            "consignment_country": self.valid_country.pk,
            "contract_sign_date": timezone.now(),
            "contract_completion_date": timezone.now(),
            "explanation": "Test explanation",
            "commodity": Commodity.objects.get(commodity_code="4402100010").pk,
            "goods_description": "Test description",
            "quantity": "1.00",
            "unit": "kilos",
            "value": "2.00",
        }
        form = SubmitDerogationsForm(data, instance=self.process, initial={"contact": self.user})

        assert form.is_valid(), form.errors

    def test_da_form_invalid_with_wrong_country(self):
        data = {
            "contact": self.user.pk,
            "origin_country": self.invalid_country.pk,
            "consignment_country": self.invalid_country.pk,
            "contract_sign_date": timezone.now(),
            "contract_completion_date": timezone.now(),
            "explanation": "Test explanation",
        }
        form = SubmitDerogationsForm(data, instance=self.process, initial={"contact": self.user})
        assert not form.is_valid()
        assert form.errors

    def test_da_form_invalid_without_required_fields(self):
        data = {}
        form = SubmitDerogationsForm(data, instance=self.process, initial={"contact": self.user})

        assert not form.is_valid()
        assert form.errors
        assert len(form.errors) == 11
