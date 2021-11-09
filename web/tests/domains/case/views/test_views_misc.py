from typing import TYPE_CHECKING

import pytest
from pytest_django.asserts import assertContains, assertTemplateUsed

from web.domains.case._import.models import ImportApplication
from web.flow.errors import ProcessStateError
from web.flow.models import Task
from web.tests.helpers import CaseURLS

if TYPE_CHECKING:
    from django.test.client import Client

    from web.domains.case._import.wood.models import WoodQuotaApplication


def test_take_ownership(icms_admin_client: "Client", wood_app_submitted):
    resp = icms_admin_client.post(CaseURLS.take_ownership(wood_app_submitted.pk))
    assert resp.status_code == 302

    wood_app_submitted.refresh_from_db()
    assert wood_app_submitted.get_task(ImportApplication.Statuses.PROCESSING, Task.TaskType.PROCESS)


def test_take_ownership_in_progess(icms_admin_client: "Client", wood_app_in_progress):
    # Can't own an in progress application
    with pytest.raises(ProcessStateError):
        icms_admin_client.post(CaseURLS.take_ownership(wood_app_in_progress.pk))


def test_manage_case_get(icms_admin_client: "Client", wood_app_submitted):
    resp = icms_admin_client.get(CaseURLS.manage(wood_app_submitted.pk))

    assert resp.status_code == 200
    assertContains(resp, "Wood (Quota) - Manage")
    assertTemplateUsed(resp, "web/domains/case/manage/manage.html")


# def test_manage_case_post():
#     # TODO: Add a test to stop a case
#     ...


def test_manage_withdrawals_get(
    icms_admin_client: "Client", wood_app_submitted: "WoodQuotaApplication"
):
    resp = icms_admin_client.get(CaseURLS.manage_withdrawals(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Withdrawals")
    assertTemplateUsed(resp, "web/domains/case/manage/withdrawals.html")

    assert resp.context["withdrawals"].count() == 0
    assert resp.context["current_withdrawal"] is None


# def test_manage_withdrawals_post():
#     # TODO: Add test for approving a withdrawal
#     # TODO: Add test to reject a withdrawal
#     ...
