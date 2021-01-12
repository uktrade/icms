from django.urls import reverse
from guardian.shortcuts import assign_perm

from web.domains.case._import.models import (
    ImportApplicationType,
    OpenIndividualLicenceApplication,
)
from web.tests.auth import AuthTestCase
from web.tests.domains.case._import.factory import OILApplicationFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.office.factory import OfficeFactory

LOGIN_URL = "/"


class ImportAppplicationCreateViewTest(AuthTestCase):
    url = "/import/firearms/oil/create/"
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
        OILApplicationFactory.create()

        office = OfficeFactory.create(is_active=True)
        importer = ImporterFactory.create(is_active=True, offices=[office])
        assign_perm("web.is_contact_of_importer", self.user, importer)
        self.login_with_permissions(["importer_access"])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("create-oil"), data={"importer": importer.pk, "importer_office": office.pk}
        )

        application = OpenIndividualLicenceApplication.objects.get()
        self.assertEqual(application.process_type, OpenIndividualLicenceApplication.PROCESS_TYPE)

        application_type = application.application_type
        self.assertEqual(application_type.type, ImportApplicationType.TYPE_FIREARMS_AMMUNITION_CODE)
        self.assertEqual(
            application_type.sub_type, ImportApplicationType.SUBTYPE_OPEN_INDIVIDUAL_LICENCE
        )

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
