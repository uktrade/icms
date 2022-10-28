from unittest.mock import patch

import pytest
from django.test import override_settings

from web.domains.case._import.models import ImportApplicationType
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import ApplicationBase, UpdateRequest, WithdrawApplication
from web.domains.workbasket.base import WorkbasketSection
from web.domains.workbasket.views import _add_user_import_annotations
from web.flow.models import Task


@pytest.fixture
def app_in_progress(db, importer, test_import_user):
    app = _create_wood_app(importer, test_import_user, ApplicationBase.Statuses.IN_PROGRESS)
    return _get_wood_app_with_annotations(app)


@pytest.fixture
def app_submitted(db, importer, test_import_user):
    app = _create_wood_app(importer, test_import_user, ApplicationBase.Statuses.SUBMITTED)
    return _get_wood_app_with_annotations(app)


@pytest.fixture
def app_processing(db, importer, test_import_user, test_icms_admin_user):
    app = _create_wood_app(
        importer,
        test_import_user,
        ApplicationBase.Statuses.PROCESSING,
        case_owner=test_icms_admin_user,
    )

    Task.objects.create(process=app, task_type=Task.TaskType.PROCESS)

    return _get_wood_app_with_annotations(app)


@pytest.fixture
def app_completed(db, importer, test_import_user):
    app = _create_wood_app(importer, test_import_user, ApplicationBase.Statuses.COMPLETED)
    return _get_wood_app_with_annotations(app)


@pytest.fixture
def app_completed_agent(db, importer, test_agent_import_user, agent_importer):
    app = _create_wood_app(
        importer, test_agent_import_user, ApplicationBase.Statuses.COMPLETED, agent=agent_importer
    )
    return _get_wood_app_with_annotations(app)


def test_actions_in_progress(app_in_progress, test_import_user):
    user_row = app_in_progress.get_workbasket_row(test_import_user, False)

    _check_actions(user_row.sections, expected_actions={"Resume", "Cancel"})


def test_actions_submitted(app_submitted, test_import_user):
    user_row = app_submitted.get_workbasket_row(test_import_user, False)

    _check_actions(user_row.sections, expected_actions={"Request Withdrawal", "View Application"})


def test_actions_processing(app_processing, test_import_user):
    user_row = app_processing.get_workbasket_row(test_import_user, False)

    _check_actions(user_row.sections, expected_actions={"Request Withdrawal", "View Application"})


def test_actions_fir_withdrawal_update_request(app_processing, test_import_user):
    # fetch the app to refresh the annotations after creating a fir withdrawal
    _create_fir_withdrawal(app_processing, test_import_user)
    app_processing = _get_wood_app_with_annotations(app_processing)

    user_row = app_processing.get_workbasket_row(test_import_user, False)
    _check_actions(
        user_row.sections,
        expected_actions={"Pending Withdrawal", "View Application", "Respond"},
    )

    _create_update_request(app_processing)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    user_row = app_processing.get_workbasket_row(test_import_user, False)

    _check_actions(
        user_row.sections,
        expected_actions={
            "Pending Withdrawal",
            "View Application",
            "Respond",
            "Respond to Update Request",
        },
    )


def test_actions_authorise(app_processing, test_import_user):
    _update_task(app_processing, Task.TaskType.AUTHORISE)
    user_row = app_processing.get_workbasket_row(test_import_user, False)

    _check_actions(user_row.sections, expected_actions={"Request Withdrawal", "View Application"})


@override_settings(ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD=True)
def test_actions_bypass_chief(app_processing, test_import_user):
    _update_task(app_processing, Task.TaskType.CHIEF_WAIT)
    user_row = app_processing.get_workbasket_row(test_import_user, False)

    _check_actions(user_row.sections, expected_actions={"Request Withdrawal", "View Application"})

    _update_task(app_processing, Task.TaskType.CHIEF_ERROR)
    user_row = app_processing.get_workbasket_row(test_import_user, False)

    _check_actions(user_row.sections, expected_actions={"Request Withdrawal", "View Application"})


def test_actions_completed(app_completed, test_import_user):
    user_row = app_completed.get_workbasket_row(test_import_user, False)

    _check_actions(
        user_row.sections,
        expected_actions={"View Application", "Clear"},
    )


def test_admin_actions_in_progress_ilb_admin(app_in_progress, test_icms_admin_user):
    admin_row = app_in_progress.get_workbasket_row(test_icms_admin_user, True)

    assert admin_row.sections == []


def test_admin_actions_submitted(app_submitted, test_icms_admin_user):
    admin_row = app_submitted.get_workbasket_row(test_icms_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Take Ownership", "View"})

    _test_view_endpoint_is_case_management(app_submitted, admin_row.sections)


def test_admin_actions_processing(app_processing, test_icms_admin_user):
    admin_row = app_processing.get_workbasket_row(test_icms_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Manage"})


def test_admin_actions_fir_withdrawal_update_request(
    app_processing, test_import_user, test_icms_admin_user
):
    _create_fir_withdrawal(app_processing, test_import_user)
    admin_row = app_processing.get_workbasket_row(test_icms_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Manage"})

    _create_update_request(app_processing)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    admin_row = app_processing.get_workbasket_row(test_icms_admin_user, True)

    assert admin_row.sections == []


def test_admin_actions_authorise(app_processing, test_icms_admin_user):
    _update_task(app_processing, Task.TaskType.AUTHORISE)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    admin_row = app_processing.get_workbasket_row(test_icms_admin_user, True)

    _check_actions(
        admin_row.sections,
        expected_actions={"Cancel Authorisation", "Authorise Documents", "View Case"},
    )

    _test_view_endpoint_is_case_management(app_processing, admin_row.sections, "View Case")


@override_settings(ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD=True)
def test_admin_actions_bypass_chief(app_processing, test_icms_admin_user):
    _update_task(app_processing, Task.TaskType.CHIEF_WAIT)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    # bypass-chief urls are not included
    with patch("web.domains.case.models.reverse"):
        admin_row = app_processing.get_workbasket_row(test_icms_admin_user, True)

    _check_actions(
        admin_row.sections,
        expected_actions={
            "(TEST) Bypass CHIEF induce failure",
            "(TEST) Bypass CHIEF",
            "Monitor Progress",
            "View",
        },
    )

    _test_view_endpoint_is_case_management(app_processing, admin_row.sections)

    _update_task(app_processing, Task.TaskType.CHIEF_ERROR)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    admin_row = app_processing.get_workbasket_row(test_icms_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Show Licence Details", "View"})
    _test_view_endpoint_is_case_management(app_processing, admin_row.sections)


def test_admin_actions_completed(app_completed, test_icms_admin_user):
    admin_row = app_completed.get_workbasket_row(test_icms_admin_user, True)

    # By default the admin shouldn't see anything
    assert len(admin_row.sections) == 0

    # Reject an application to see admin "Completed" actions
    app_completed.case_owner = test_icms_admin_user
    app_completed.save()
    Task.objects.create(process=app_completed, task_type=Task.TaskType.REJECTED, previous=None)

    admin_row = app_completed.get_workbasket_row(test_icms_admin_user, True)
    _check_actions(admin_row.sections, expected_actions={"View Case", "Clear"})


def _check_actions(sections: list[WorkbasketSection], expected_actions: set[str]):
    """Combine all the actions in each section and test equal to the expected actions"""
    all_actions = set()

    for section in sections:
        actions = section.actions
        row_actions = {r.name for r in actions}
        all_actions.update(row_actions)

    assert all_actions == expected_actions


def _create_fir_withdrawal(app, test_import_user):
    app.further_information_requests.create(
        process_type=FurtherInformationRequest.PROCESS_TYPE, status=FurtherInformationRequest.OPEN
    )

    app.withdrawals.create(status=WithdrawApplication.STATUS_OPEN, request_by=test_import_user)


def _create_update_request(app):
    app.update_requests.create(status=UpdateRequest.Status.OPEN)
    _update_task(app, Task.TaskType.PREPARE)


def _update_task(app, new_task_type):
    task = app.get_active_tasks().first()
    task.is_active = False
    task.save()
    Task.objects.create(process=app, task_type=new_task_type, previous=task)


def _create_wood_app(importer, test_import_user, status, agent=None, case_owner=None):
    return WoodQuotaApplication.objects.create(
        process_type=WoodQuotaApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.WOOD_QUOTA
        ),
        importer=importer,
        agent=agent,
        created_by=test_import_user,
        last_updated_by=test_import_user,
        status=status,
        case_owner=case_owner,
    )


def _test_view_endpoint_is_case_management(application, sections, view_label="View"):
    # Check the view endpoint is the management link
    for section in sections:
        for action in section.actions:
            if action.name == view_label:
                assert action.url == f"/case/import/{application.pk}/admin/manage/"
                return

    raise ValueError("Failed to find view ")


def _get_wood_app_with_annotations(app):
    """Return a WoodQuotaApplication instance with the correct workbasket annotations"""
    return _add_user_import_annotations(WoodQuotaApplication.objects.filter(pk=app.pk)).get()
