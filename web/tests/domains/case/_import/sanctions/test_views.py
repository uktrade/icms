from django.urls import reverse
from guardian.shortcuts import assign_perm

from web.domains.case._import.models import ImportApplicationType
from web.domains.case._import.sanctions.models import SanctionsAndAdhocApplication
from web.domains.importer.models import Importer
from web.tests.auth import AuthTestCase
from web.tests.domains.case._import.factory import (
    SanctionsAndAdhocLicenseApplicationFactory,
    SanctionsAndAdhocLicenseApplicationTypeFactory,
)
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.office.factory import OfficeFactory
from web.tests.flow.factories import TaskFactory

LOGIN_URL = "/"


class SanctionsAndAdhocImportAppplicationCreateViewTest(AuthTestCase):
    url = "/import/create/sanctions/"
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
        SanctionsAndAdhocLicenseApplicationTypeFactory.create()
        office = OfficeFactory.create(is_active=True)
        importer = ImporterFactory.create(is_active=True, offices=[office])

        assign_perm("web.is_contact_of_importer", self.user, importer)

        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        self.client.post(
            reverse("import:create-sanctions"),
            data={"importer": importer.pk, "importer_office": office.pk},
        )
        application = SanctionsAndAdhocApplication.objects.get()
        self.assertEqual(application.process_type, SanctionsAndAdhocApplication.PROCESS_TYPE)

        application_type = application.application_type
        self.assertEqual(application_type.type, ImportApplicationType.TYPE_SANCTION_ADHOC)

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


class SanctionsAndAdhocImportAppplicationApplicantDetailsTest(AuthTestCase):
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

        IN_PROGRESS = "IN_PROGRESS"
        self.process = SanctionsAndAdhocLicenseApplicationFactory.create(
            status=IN_PROGRESS,
            importer=self.importer,
            created_by=self.user,
            last_updated_by=self.user,
        )
        TaskFactory.create(process=self.process, task_type="prepare")
        self.url = f"/import/sanctions/{self.process.pk}/edit"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

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
