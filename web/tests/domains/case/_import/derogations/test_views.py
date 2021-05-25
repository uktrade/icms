from datetime import date

from django.urls import reverse
from guardian.shortcuts import assign_perm

from web.domains.case._import.derogations.models import DerogationsApplication
from web.domains.case._import.models import ImportApplicationType
from web.domains.country.models import Country
from web.domains.importer.models import Importer
from web.tests.auth import AuthTestCase
from web.tests.domains.case._import.factory import DerogationsApplicationFactory
from web.tests.domains.commodity.factory import CommodityTypeFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.office.factory import OfficeFactory
from web.tests.flow.factories import TaskFactory

LOGIN_URL = "/"


class DerogationAppplicationCreateViewTest(AuthTestCase):
    url = "/import/create/derogations/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_create_ok(self):
        office = OfficeFactory.create(is_active=True)
        importer = ImporterFactory.create(is_active=True, offices=[office])

        assign_perm("web.is_contact_of_importer", self.user, importer)
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.client.post(
            reverse("import:create-derogations"),
            data={"importer": importer.pk, "importer_office": office.pk},
        )
        application = DerogationsApplication.objects.get()
        self.assertEqual(application.process_type, DerogationsApplication.PROCESS_TYPE)

        application_type = application.application_type
        self.assertEqual(application_type.type, ImportApplicationType.Types.DEROGATION)

        task = application.tasks.get()
        self.assertEqual(task.task_type, "prepare")
        self.assertEqual(task.is_active, True)

    def test_anonymous_post_access_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_forbidden_post_access(self):
        self.login()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)


class DegrogationDetailsViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.importer_name = "Importer Limited"
        self.importer_eori = "GB3423453234"

        self.importer = ImporterFactory.create(
            type=Importer.ORGANISATION,
            user=self.user,
            name=self.importer_name,
            eori_number=self.importer_eori,
        )

        self.process = DerogationsApplicationFactory.create(
            status="IN_PROGRESS",
            importer=self.importer,
            created_by=self.user,
            last_updated_by=self.user,
        )

        TaskFactory.create(process=self.process, task_type="prepare")
        self.url = f"/import/derogations/{self.process.pk}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

        self.valid_country = Country.objects.filter(
            country_groups__name="Derogation from Sanctions COOs"
        ).first()

        self.commodity_type = CommodityTypeFactory.create()

        assign_perm("web.is_contact_of_importer", self.user, self.importer)

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_logged_in_permissions(self):
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.url)
        assert response.status_code == 200

    def test_page_content(self):
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.url)
        assert self.importer_name in response.content.decode()
        assert self.importer_eori in response.content.decode()

    def test_save_application_details(self):
        self.login_with_permissions(["importer_access"])
        app_ref = "REF64563343"
        contract_sign_date = date.today()
        contract_completion_date = date.today()
        data = {
            "contact": self.user.pk,
            "applicant_reference": app_ref,
            "origin_country": self.valid_country.pk,
            "consignment_country": self.valid_country.pk,
            "contract_sign_date": contract_sign_date.strftime("%d-%b-%Y"),
            "contract_completion_date": contract_completion_date.strftime("%d-%b-%Y"),
            "explanation": "Test explanation",
            "commodity_code": "4403201110",
            "goods_description": "Test description",
            "quantity": "1.00",
            "unit": "kilos",
            "value": "2.00",
        }
        self.client.post(
            reverse("import:derogations:edit", kwargs={"application_pk": self.process.pk}),
            data=data,
        )
        response = self.client.get(self.url)

        assert response.status_code == 200
        application = DerogationsApplication.objects.get(pk=self.process.pk)
        assert application.contact == self.user
        assert application.applicant_reference == app_ref
        assert application.origin_country == self.valid_country
        assert application.consignment_country == self.valid_country
        assert application.contract_sign_date == contract_sign_date
        assert application.contract_completion_date == contract_completion_date
