from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed

from web.models import FurtherInformationRequest, Task
from web.tests.auth import AuthTestCase
from web.tests.domains.case.access.factories import ImporterAccessRequestFactory
from web.tests.flow.factories import TaskFactory
from web.tests.helpers import CaseURLS

if TYPE_CHECKING:
    from django.test.client import Client

    from web.models import WoodQuotaApplication


def test_manage_update_requests_get(
    icms_admin_client: "Client", wood_app_submitted: "WoodQuotaApplication"
) -> None:
    resp = icms_admin_client.get(CaseURLS.manage_firs(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Further Information Requests")
    assertTemplateUsed(resp, "web/domains/case/manage/list-firs.html")

    assert resp.context["firs"].count() == 0


# def test_manage_update_requests_post():
#     # TODO: Add test for sending an update request
#     ...


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


class TestImporterAccessRequestFIRListView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.process = ImporterAccessRequestFactory(
            link=self.importer, submitted_by=self.importer_user
        )

        TaskFactory.create(process=self.process, task_type=Task.TaskType.PROCESS)
        self.fir_process = _create_further_information_request(self.ilb_admin_user)
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
        second_fir = _create_further_information_request(
            self.ilb_admin_user, status=FurtherInformationRequest.DELETED, is_active=False
        )

        self.process.further_information_requests.add(second_fir)
        response = self.importer_client.get(self.url)

        assert response.status_code == 200
        fir_list = response.context["firs"]
        assert len(fir_list) == 1
        assert fir_list.first() == self.fir_process
