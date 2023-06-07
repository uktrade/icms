from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed

from web.models import FurtherInformationRequest
from web.tests.auth import AuthTestCase
from web.tests.helpers import CaseURLS

if TYPE_CHECKING:
    from django.test.client import Client

    from web.models import Process, WoodQuotaApplication


def _create_fir(
    process: "Process", ilb_admin_client: "Client", case_type: str, subject: str = "test_subject"
):
    resp = ilb_admin_client.post(CaseURLS.add_fir(process.pk, case_type))

    ilb_admin_client.post(
        resp.url,
        {
            "status": "DRAFT",
            "request_subject": subject,
            "request_detail": "test request detail",
            "send": "",
        },
    )

    return FurtherInformationRequest.objects.get(request_subject=subject)


class TestManageFirsView(AuthTestCase):
    def _add_fir_to_app(
        self, application: "Process", case_type: str = "import"
    ) -> FurtherInformationRequest:
        fir = _create_fir(application, self.ilb_admin_client, case_type)

        return fir

    def test_permission(self, fa_dfl_app_submitted):
        app = fa_dfl_app_submitted
        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
        url = CaseURLS.manage_firs(app.pk, "import")

        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_manage_import_application_fir(self, fa_dfl_app_submitted):
        app = fa_dfl_app_submitted
        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
        url = CaseURLS.manage_firs(app.pk, "import")

        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["process"].get_specific_model() == app
        assert context["case_type"] == "import"
        assert context["firs"].count() == 0

        fir = self._add_fir_to_app(app)

        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["firs"].count() == 1
        assert context["firs"][0] == fir

    def test_manage_export_application_fir(self, com_app_submitted):
        app = com_app_submitted

        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))
        url = CaseURLS.manage_firs(app.pk, "export")

        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["process"].get_specific_model() == app
        assert context["case_type"] == "export"
        assert context["firs"].count() == 0

        fir = self._add_fir_to_app(app, "export")

        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["firs"].count() == 1
        assert context["firs"][0] == fir

    def test_manage_importer_access_request_fir(self, importer_access_request):
        app = importer_access_request

        url = CaseURLS.manage_firs(app.pk, "access")
        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["case_type"] == "access"
        assert context["firs"].count() == 0

        fir = self._add_fir_to_app(app, "access")

        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["firs"].count() == 1
        assert context["firs"][0] == fir

    def test_manage_exporter_access_request_fir(self, exporter_access_request):
        app = exporter_access_request

        url = CaseURLS.manage_firs(app.pk, "access")
        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["case_type"] == "access"
        assert context["firs"].count() == 0

        fir = self._add_fir_to_app(app, "access")

        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["firs"].count() == 1
        assert context["firs"][0] == fir


def test_manage_update_requests_get(
    ilb_admin_client: "Client", wood_app_submitted: "WoodQuotaApplication"
) -> None:
    resp = ilb_admin_client.get(CaseURLS.manage_firs(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Further Information Requests")
    assertTemplateUsed(resp, "web/domains/case/manage/list-firs.html")

    assert resp.context["firs"].count() == 0


# def test_manage_update_requests_post():
#     # TODO: Add test for sending an update request
#     ...


class TestImporterAccessRequestFIRListView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, importer_access_request):
        self.process = importer_access_request
        self.process.link = self.importer
        self.process.submitted_by = self.importer_user
        self.process.save()

        self.fir_process = _create_fir(self.process, self.ilb_admin_client, "access")
        self.process.further_information_requests.add(self.fir_process)

        self.url = reverse(
            "case:list-firs", kwargs={"application_pk": self.process.pk, "case_type": "access"}
        )

    def test_forbidden_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 200

    def test_deleted_firs_not_shown(self):
        fir = _create_fir(self.process, self.ilb_admin_client, "access", "test delete")
        self.ilb_admin_client.post(CaseURLS.delete_fir(self.process.pk, fir.pk, "access"))

        response = self.importer_client.get(self.url)

        assert response.status_code == 200
        fir_list = response.context["firs"]
        assert len(fir_list) == 1
        assert fir_list.first() == self.fir_process
