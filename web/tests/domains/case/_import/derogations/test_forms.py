from django.utils import timezone
from guardian.shortcuts import assign_perm

from web.domains.case._import.derogations.forms import SubmitDerogationsForm
from web.domains.commodity.models import Commodity
from web.domains.country.models import Country
from web.domains.importer.models import Importer
from web.flow.models import Task
from web.tests.auth import AuthTestCase
from web.tests.domains.case._import.factory import DerogationsApplicationFactory
from web.tests.domains.commodity.factory import CommodityTypeFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.flow.factories import TaskFactory


class DerogationsFormTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        Country.objects.filter(country_groups__name="Derogation from Sanctions COOs")

        self.valid_country = Country.objects.filter(
            country_groups__name="Derogation from Sanctions COOs"
        ).first()
        self.invalid_country = Country.objects.exclude(
            country_groups__name="Derogation from Sanctions COOs"
        ).first()

        self.importer = ImporterFactory.create(
            type=Importer.ORGANISATION,
            user=self.user,
            name="Importer Limited",
            eori_number="GB3423453234",
        )
        self.process = DerogationsApplicationFactory.create(
            status="IN_PROGRESS",
            importer=self.importer,
            created_by=self.user,
            last_updated_by=self.user,
        )
        TaskFactory.create(process=self.process, task_type=Task.TaskType.PREPARE)

        assign_perm("web.is_contact_of_importer", self.user, self.importer)
        self.login_with_permissions(["importer_access"])

        self.commodity_type = CommodityTypeFactory.create()

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
        self.assertTrue(form.is_valid(), form.errors)

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
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)

    def test_da_form_invalid_without_required_fields(self):
        data = {}
        form = SubmitDerogationsForm(data, instance=self.process, initial={"contact": self.user})
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
        self.assertEqual(len(form.errors), 11)
