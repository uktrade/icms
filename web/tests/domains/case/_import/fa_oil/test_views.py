import pytest
from django.test import Client
from django.urls import reverse
from guardian.shortcuts import assign_perm

from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
from web.domains.case._import.models import ImportApplicationType
from web.domains.importer.models import Importer
from web.tests.auth import AuthTestCase
from web.tests.domains.case._import.factory import OILApplicationFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.office.factory import OfficeFactory
from web.tests.domains.user.factory import ActiveUserFactory
from web.tests.flow.factories import TaskFactory

LOGIN_URL = "/"


class ImportAppplicationCreateViewTest(AuthTestCase):
    url = "/import/create/firearms/oil/"
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
            reverse("import:create-fa-oil"),
            data={"importer": importer.pk, "importer_office": office.pk},
        )
        application = OpenIndividualLicenceApplication.objects.get()
        self.assertEqual(application.process_type, OpenIndividualLicenceApplication.PROCESS_TYPE)

        application_type = application.application_type
        self.assertEqual(application_type.type, ImportApplicationType.Types.FIREARMS)
        self.assertEqual(application_type.sub_type, ImportApplicationType.SubTypes.OIL)

        task = application.tasks.get()
        self.assertEqual(task.task_type, "prepare")
        self.assertEqual(task.is_active, True)

    def test_create_missing_office(self):
        office = OfficeFactory.create(is_active=True)
        importer = ImporterFactory.create(is_active=True, offices=[office])
        assign_perm("web.is_contact_of_importer", self.user, importer)
        self.login_with_permissions(["importer_access"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("import:create-fa-oil"), data={"importer": importer.pk})
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<div class="error-message">You must enter this item', response.content.decode("utf-8")
        )

    def test_anonymous_post_access_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_forbidden_post_access(self):
        self.login()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)


@pytest.mark.django_db
def test_take_ownership():
    user = ActiveUserFactory.create(permission_codenames=["importer_access"])
    importer = ImporterFactory.create(type=Importer.ORGANISATION, user=user)

    process = OILApplicationFactory.create(
        status="SUBMITTED", importer=importer, created_by=user, last_updated_by=user
    )
    TaskFactory.create(process=process, task_type="process")

    ilb_admin = ActiveUserFactory.create(permission_codenames=["reference_data_access"])
    client = Client()
    client.login(username=ilb_admin.username, password="test")
    response_workbasket = client.get("/workbasket/")
    assert "Take Ownership" in response_workbasket.content.decode()

    # After taking ownership we now navigate to the case management "view application" view.
    response = client.post(f"/case/import/{process.pk}/admin/take-ownership/", follow=True)

    assert response.status_code == 200
    view_application_response = response.content.decode()
    assert "Firearms and Ammunition Open Individual Import Licence" in view_application_response


@pytest.mark.django_db
def test_release_ownership():
    ilb_admin = ActiveUserFactory.create(permission_codenames=["reference_data_access"])
    user = ActiveUserFactory.create(permission_codenames=["importer_access"])
    importer = ImporterFactory.create(type=Importer.ORGANISATION, user=user)

    process = OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        created_by=user,
        last_updated_by=user,
        case_owner=ilb_admin,
    )
    TaskFactory.create(process=process, task_type="process")

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    response = client.post(f"/case/import/{process.pk}/admin/release-ownership/", follow=True)
    assert "Manage" in response.content.decode()


@pytest.mark.django_db
def test_close_case():
    ilb_admin = ActiveUserFactory.create(permission_codenames=["reference_data_access"])
    user = ActiveUserFactory.create(permission_codenames=["importer_access"])
    importer = ImporterFactory.create(type=Importer.ORGANISATION, user=user)

    process = OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        created_by=user,
        last_updated_by=user,
        case_owner=ilb_admin,
    )
    task = TaskFactory.create(process=process, task_type="process")

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    client.post(f"/case/import/{process.pk}/admin/manage/", data={"send_email": True}, follow=True)

    process.refresh_from_db()
    assert process.status == "STOPPED"

    task.refresh_from_db()
    assert task.is_active is False
