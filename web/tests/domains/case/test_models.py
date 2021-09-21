import pytest
from django.test import override_settings

from web.domains.case._import.models import ImportApplicationType
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import ApplicationBase, UpdateRequest, WithdrawApplication
from web.domains.workbasket.base import WorkbasketAction
from web.flow.models import Task

pytestmark = pytest.mark.django_db


@pytest.fixture
def app_in_progress(importer, test_import_user):
    return _create_wood_app(importer, test_import_user, ApplicationBase.Statuses.IN_PROGRESS)


@pytest.fixture
def app_submitted(importer, test_import_user):
    return _create_wood_app(importer, test_import_user, ApplicationBase.Statuses.SUBMITTED)


@pytest.fixture
def app_processing(importer, test_import_user, test_icms_admin_user):
    app = _create_wood_app(
        importer,
        test_import_user,
        ApplicationBase.Statuses.PROCESSING,
        case_owner=test_icms_admin_user,
    )

    Task.objects.create(process=app, task_type=Task.TaskType.PROCESS)

    return app


@pytest.fixture
def app_completed(importer, test_import_user):
    return _create_wood_app(importer, test_import_user, ApplicationBase.Statuses.COMPLETED)


@pytest.fixture
def completed(importer, test_import_user):
    _create_wood_app(importer, test_import_user, ApplicationBase.Statuses.COMPLETED)


def test_actions_in_progress(app_in_progress, test_import_user):
    user_row = app_in_progress.get_workbasket_row(test_import_user)

    _check_actions(user_row.actions, expected_names={"Resume", "Cancel"})


def test_actions_submitted(app_submitted, test_import_user):
    user_row = app_submitted.get_workbasket_row(test_import_user)

    _check_actions(user_row.actions, expected_names={"Request Withdrawal", "View"})


def test_actions_processing(app_processing, test_import_user):
    user_row = app_processing.get_workbasket_row(test_import_user)

    _check_actions(user_row.actions, expected_names={"Request Withdrawal", "View"})


def test_actions_fir_withdrawal_update_request(app_processing, test_import_user):
    _create_fir_withdrawal(app_processing, test_import_user)
    user_row = app_processing.get_workbasket_row(test_import_user)

    _check_actions(
        user_row.actions,
        expected_names={"Pending Withdrawal", "View", "Respond FIR"},
    )

    _create_update_request(app_processing)
    user_row = app_processing.get_workbasket_row(test_import_user)

    _check_actions(
        user_row.actions,
        expected_names={"Pending Withdrawal", "View", "Respond FIR", "Respond to Update Request"},
    )


def test_actions_authorise(app_processing, test_import_user):
    _update_task(app_processing, Task.TaskType.AUTHORISE)
    user_row = app_processing.get_workbasket_row(test_import_user)

    _check_actions(user_row.actions, expected_names={"Request Withdrawal", "View"})


@override_settings(ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD=True)
def test_actions_bypass_chief(app_processing, test_import_user):
    _update_task(app_processing, Task.TaskType.CHIEF_WAIT)
    user_row = app_processing.get_workbasket_row(test_import_user)

    _check_actions(user_row.actions, expected_names={"Request Withdrawal", "View"})

    _update_task(app_processing, Task.TaskType.CHIEF_ERROR)
    user_row = app_processing.get_workbasket_row(test_import_user)

    _check_actions(user_row.actions, expected_names={"Request Withdrawal", "View"})


def test_actions_acknowledge(app_processing, test_import_user):
    _update_task(app_processing, Task.TaskType.ACK)
    user_row = app_processing.get_workbasket_row(test_import_user)

    _check_actions(user_row.actions, expected_names={"Request Withdrawal", "View"})


def test_actions_completed(app_completed, test_import_user):
    user_row = app_completed.get_workbasket_row(test_import_user)

    _check_actions(user_row.actions, expected_names={"Acknowledge Notification", "View"})


@override_settings(DEBUG_SHOW_ALL_WORKBASKET_ROWS=False)
def test_admin_actions_in_progress_ilb_admin(app_in_progress, test_icms_admin_user):
    admin_row = app_in_progress.get_workbasket_row(test_icms_admin_user)

    assert admin_row.actions == []


@override_settings(DEBUG_SHOW_ALL_WORKBASKET_ROWS=False)
def test_admin_actions_submitted(app_submitted, test_icms_admin_user):
    admin_row = app_submitted.get_workbasket_row(test_icms_admin_user)

    _check_actions(admin_row.actions, expected_names={"Take Ownership", "View"})


@override_settings(DEBUG_SHOW_ALL_WORKBASKET_ROWS=False)
def test_admin_actions_processing(app_processing, test_icms_admin_user):
    admin_row = app_processing.get_workbasket_row(test_icms_admin_user)

    _check_actions(admin_row.actions, expected_names={"Manage"})


@override_settings(DEBUG_SHOW_ALL_WORKBASKET_ROWS=False)
def test_admin_actions_fir_withdrawal_update_request(
    app_processing, test_import_user, test_icms_admin_user
):
    _create_fir_withdrawal(app_processing, test_import_user)
    admin_row = app_processing.get_workbasket_row(test_icms_admin_user)

    _check_actions(admin_row.actions, expected_names={"Manage"})

    _create_update_request(app_processing)
    admin_row = app_processing.get_workbasket_row(test_icms_admin_user)

    assert admin_row.actions == []


@override_settings(DEBUG_SHOW_ALL_WORKBASKET_ROWS=False)
def test_admin_actions_authorise(app_processing, test_icms_admin_user):
    _update_task(app_processing, Task.TaskType.AUTHORISE)
    admin_row = app_processing.get_workbasket_row(test_icms_admin_user)

    _check_actions(
        admin_row.actions, expected_names={"Cancel Authorisation", "Authorise Documents", "View"}
    )


@override_settings(
    DEBUG_SHOW_ALL_WORKBASKET_ROWS=False, ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD=True
)
def test_admin_actions_bypass_chief(app_processing, test_icms_admin_user):
    _update_task(app_processing, Task.TaskType.CHIEF_WAIT)
    admin_row = app_processing.get_workbasket_row(test_icms_admin_user)

    _check_actions(
        admin_row.actions,
        expected_names={
            "(TEST) Bypass CHIEF induce failure",
            "(TEST) Bypass CHIEF",
            "Monitor Progress",
            "View",
        },
    )

    _update_task(app_processing, Task.TaskType.CHIEF_ERROR)
    admin_row = app_processing.get_workbasket_row(test_icms_admin_user)

    _check_actions(admin_row.actions, expected_names={"Show Licence Details", "View"})


@override_settings(DEBUG_SHOW_ALL_WORKBASKET_ROWS=False)
def test_admin_actions_acknowledge(app_processing, test_icms_admin_user):
    _update_task(app_processing, Task.TaskType.ACK)
    admin_row = app_processing.get_workbasket_row(test_icms_admin_user)

    assert admin_row.actions == []


@override_settings(DEBUG_SHOW_ALL_WORKBASKET_ROWS=False)
def test_admin_actions_completed(app_completed, test_icms_admin_user):
    admin_row = app_completed.get_workbasket_row(test_icms_admin_user)

    _check_actions(admin_row.actions, expected_names={"View"})


def _check_actions(actions: list[list[WorkbasketAction]], expected_names: set[str]):
    # Only one set of actions
    assert len(actions) == 1, f"One action expected but {len(actions)} passed"

    row_actions = {r.name for r in actions[0]}
    assert row_actions == expected_names


def _create_fir_withdrawal(app, test_import_user):
    app.further_information_requests.create(
        process_type=FurtherInformationRequest.PROCESS_TYPE, status=FurtherInformationRequest.OPEN
    )

    app.withdrawals.create(status=WithdrawApplication.STATUS_OPEN, request_by=test_import_user)


def _create_update_request(app):
    app.update_requests.create(status=UpdateRequest.Status.OPEN)
    _update_task(app, Task.TaskType.PREPARE)


def _update_task(app, new_task_type):
    task = app.get_active_task()
    task.is_active = False
    task.save()
    Task.objects.create(process=app, task_type=new_task_type, previous=task)


def _create_wood_app(importer, test_import_user, status, case_owner=None):
    return WoodQuotaApplication.objects.create(
        process_type=WoodQuotaApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.WOOD_QUOTA
        ),
        importer=importer,
        created_by=test_import_user,
        last_updated_by=test_import_user,
        status=status,
        case_owner=case_owner,
    )
