import pytest
from django.test import Client

from web.models import FurtherInformationRequest, Task
from web.tests.auth import AuthTestCase
from web.tests.domains.case.access import factories as access_factories
from web.tests.domains.case.fir import factory as fir_factories
from web.tests.domains.user.factory import ActiveUserFactory
from web.tests.flow import factories as process_factories

LOGIN_URL = "/"


class AccessRequestTestBase(AuthTestCase):
    def setUp(self):
        super().setUp()

        # TODO: figure out how to parametrize across importer/exporter
        if True:
            self.process = access_factories.ImporterAccessRequestFactory()
        else:
            self.process = access_factories.ExporterAccessRequestFactory()

        process_factories.TaskFactory.create(process=self.process, task_type=Task.TaskType.PROCESS)
        self.fir_process = fir_factories.FurtherInformationRequestFactory()
        self.process.further_information_requests.add(self.fir_process)

        # TODO: different tests might need different url
        self.url = f"/case/access/{self.process.pk}/firs/list/"

        self.redirect_url = f"{LOGIN_URL}?next={self.url}"


# TODO: figure out how to parametrize across importer/exporter
class ImporterAccessRequestFIRListViewTest(AccessRequestTestBase):
    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_deleted_firs_not_shown(self):
        self.second_fir = fir_factories.FurtherInformationRequestFactory(
            is_active=False, status=FurtherInformationRequest.DELETED
        )
        self.process.further_information_requests.add(self.second_fir)
        self.login_with_permissions(["ilb_admin"])
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        fir_list = response.context["firs"]
        self.assertEqual(len(fir_list), 1)
        self.assertEqual(fir_list.first(), self.fir_process)


@pytest.mark.django_db
def test_list_importer_access_request_ok():
    client = Client()

    user = ActiveUserFactory.create()
    client.login(username=user.username, password="test")
    response = client.get("/access/importer/")

    assert response.status_code == 403

    ilb_admin = ActiveUserFactory.create(permission_codenames=["ilb_admin"])
    access_factories.ImporterAccessRequestFactory.create()
    client.login(username=ilb_admin.username, password="test")
    response = client.get("/access/importer/")

    assert response.status_code == 200
    assert "Search Importer Access Requests" in response.content.decode()


@pytest.mark.django_db
def test_list_exporter_access_request_ok():
    client = Client()

    user = ActiveUserFactory.create()
    client.login(username=user.username, password="test")
    response = client.get("/access/exporter/")

    assert response.status_code == 403

    ilb_admin = ActiveUserFactory.create(permission_codenames=["ilb_admin"])
    access_factories.ExporterAccessRequestFactory.create()
    client.login(username=ilb_admin.username, password="test")
    response = client.get("/access/exporter/")

    assert response.status_code == 200
    assert "Search Exporter Access Requests" in response.content.decode()
