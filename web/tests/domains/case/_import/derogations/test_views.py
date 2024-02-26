import datetime as dt

import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from web.forms.fields import JQUERY_DATE_FORMAT
from web.models import (
    Commodity,
    Country,
    DerogationsApplication,
    ImportApplicationType,
    Task,
)
from web.tests.auth import AuthTestCase
from web.tests.domains.case._import.factory import DerogationsApplicationFactory
from web.tests.domains.commodity.factory import CommodityTypeFactory


class TestDerogationApplicationCreateView(AuthTestCase):
    url = "/import/create/derogations/"

    def test_forbidden_access(self, exporter_client):
        response = exporter_client.get(self.url)
        assert response.status_code == 403

    def test_create_ok(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 200

        self.importer_client.post(
            reverse("import:create-derogations"),
            data={"importer": self.importer.pk, "importer_office": self.importer_office.pk},
        )
        application = DerogationsApplication.objects.get()
        assert application.process_type == DerogationsApplication.PROCESS_TYPE

        application_type = application.application_type
        assert application_type.type == ImportApplicationType.Types.DEROGATION

        task = application.tasks.get()
        assert task.task_type == Task.TaskType.PREPARE
        assert task.is_active


class TestDegrogationDetailsView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.process = DerogationsApplicationFactory.create(
            status="IN_PROGRESS",
            importer=self.importer,
            created_by=self.importer_user,
            last_updated_by=self.importer_user,
        )

        Task.objects.create(process=self.process, task_type=Task.TaskType.PREPARE)
        self.url = f"/import/derogations/{self.process.pk}/edit/"

        self.valid_country = Country.objects.filter(
            country_groups__name="Derogation from Sanctions COOs"
        ).first()

        self.commodity_type = CommodityTypeFactory.create()

    def test_forbidden_access(self, exporter_client):
        response = exporter_client.get(self.url)
        assert response.status_code == 403

    def test_logged_in_permissions(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 200

    def test_page_content(self):
        response = self.importer_client.get(self.url)
        assert self.importer.name in response.content.decode()
        assert self.importer.eori_number in response.content.decode()

    def test_save_application_details(self):
        app_ref = "REF64563343"
        contract_sign_date = dt.date.today()
        contract_completion_date = dt.date.today()
        data = {
            "contact": self.importer_user.pk,
            "applicant_reference": app_ref,
            "origin_country": self.valid_country.pk,
            "consignment_country": self.valid_country.pk,
            "contract_sign_date": contract_sign_date.strftime(JQUERY_DATE_FORMAT),
            "contract_completion_date": contract_completion_date.strftime(JQUERY_DATE_FORMAT),
            "explanation": "Test explanation",
            "commodity": Commodity.objects.get(commodity_code="4402100010").pk,
            "goods_description": "Test description",
            "quantity": "1.00",
            "unit": "kilos",
            "value": "2.00",
        }
        self.importer_client.post(
            reverse("import:derogations:edit", kwargs={"application_pk": self.process.pk}),
            data=data,
        )
        response = self.importer_client.get(self.url)

        assert response.status_code == 200
        application = DerogationsApplication.objects.get(pk=self.process.pk)
        assert application.contact == self.importer_user
        assert application.applicant_reference == app_ref
        assert application.origin_country == self.valid_country
        assert application.consignment_country == self.valid_country
        assert application.contract_sign_date == contract_sign_date
        assert application.contract_completion_date == contract_completion_date


class TestDerogationApplicationSubmitView(AuthTestCase):
    def test_template_context(self, django_assert_num_queries):
        process = DerogationsApplicationFactory.create(
            created_by=self.importer_user,
            last_updated_by=self.importer_user,
            importer=self.importer,
            status="IN_PROGRESS",
        )
        Task.objects.create(process=process, task_type=Task.TaskType.PREPARE)
        url = reverse(
            "import:derogations:submit-derogations", kwargs={"application_pk": process.pk}
        )

        response = self.importer_client.get(url)

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/case/import/import-case-submit.html")
