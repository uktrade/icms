import pytest

from web.domains.case._import.wood.models import WoodQuotaApplication
from web.flow import errors
from web.flow.models import Task
from web.tests.helpers import SearchURLS


def test_reopen_application_when_stopped(icms_admin_client, wood_app_submitted):
    wood_app_submitted.status = WoodQuotaApplication.Statuses.STOPPED
    wood_app_submitted.save()

    url = SearchURLS.reopen_case(application_pk=wood_app_submitted.pk)
    resp = icms_admin_client.post(url)

    _check_valid_response(resp, wood_app_submitted)


def test_reopen_application_when_withdrawn(icms_admin_client, wood_app_submitted):
    wood_app_submitted.status = WoodQuotaApplication.Statuses.WITHDRAWN
    wood_app_submitted.save()

    url = SearchURLS.reopen_case(application_pk=wood_app_submitted.pk)
    resp = icms_admin_client.post(url)

    _check_valid_response(resp, wood_app_submitted)


def test_reopen_application_when_processing_errors(icms_admin_client, wood_app_submitted):
    with pytest.raises(expected_exception=errors.ProcessStateError):
        url = SearchURLS.reopen_case(application_pk=wood_app_submitted.pk)
        icms_admin_client.post(url)


def test_reopen_application_unsets_caseworker(
    icms_admin_client, test_icms_admin_user, wood_app_submitted
):
    wood_app_submitted.status = WoodQuotaApplication.Statuses.STOPPED
    wood_app_submitted.case_owner = test_icms_admin_user
    wood_app_submitted.save()

    url = SearchURLS.reopen_case(application_pk=wood_app_submitted.pk)
    resp = icms_admin_client.post(url)

    _check_valid_response(resp, wood_app_submitted)
    assert wood_app_submitted.case_owner is None


def _check_valid_response(resp, application):
    assert resp.status_code == 204
    application.refresh_from_db()

    application.check_expected_status([application.Statuses.SUBMITTED])
    application.get_expected_task(Task.TaskType.PROCESS)
