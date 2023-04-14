import pytest
from pytest_django.asserts import assertRedirects

from web.models import FurtherInformationRequest, Task
from web.tests.auth import AuthTestCase
from web.tests.domains.case.access.factories import (
    ExporterAccessRequestFactory,
    ImporterAccessRequestFactory,
)
from web.tests.flow.factories import TaskFactory

LOGIN_URL = "/"


def _create_further_information_request(
    requested_by, *, status=FurtherInformationRequest.OPEN, **kwargs
):
    return FurtherInformationRequest.objects.create(
        process_type=FurtherInformationRequest.PROCESS_TYPE,
        requested_by=requested_by,
        status=status,
        request_subject="test subject",
        request_detail="test request detail",
        **kwargs,
    )


# TODO: figure out how to parametrize across importer/exporter
class TestImporterAccessRequestFIRListView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        # TODO: figure out how to parametrize across importer/exporter
        if True:
            self.process = ImporterAccessRequestFactory()
        else:
            self.process = ExporterAccessRequestFactory()

        TaskFactory.create(process=self.process, task_type=Task.TaskType.PROCESS)
        self.fir_process = _create_further_information_request(self.ilb_admin_user)
        self.process.further_information_requests.add(self.fir_process)

        # TODO: different tests might need different url
        self.url = f"/case/access/{self.process.pk}/firs/list/"

        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_deleted_firs_not_shown(self):
        second_fir = _create_further_information_request(
            self.ilb_admin_user, status=FurtherInformationRequest.DELETED, is_active=False
        )

        self.process.further_information_requests.add(second_fir)
        response = self.ilb_admin_client.get(self.url)

        assert response.status_code == 200
        fir_list = response.context["firs"]
        assert len(fir_list) == 1
        assert fir_list.first() == self.fir_process


@pytest.mark.django_db
def test_list_importer_access_request_ok(importer_client, icms_admin_client):
    response = importer_client.get("/access/importer/")
    assert response.status_code == 403

    ImporterAccessRequestFactory.create()
    response = icms_admin_client.get("/access/importer/")

    assert response.status_code == 200
    assert "Search Importer Access Requests" in response.content.decode()


@pytest.mark.django_db
def test_list_exporter_access_request_ok(exporter_client, icms_admin_client):
    response = exporter_client.get("/access/exporter/")

    assert response.status_code == 403

    ExporterAccessRequestFactory.create()
    response = icms_admin_client.get("/access/exporter/")

    assert response.status_code == 200
    assert "Search Exporter Access Requests" in response.content.decode()
