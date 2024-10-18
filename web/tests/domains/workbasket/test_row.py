import pytest
from django.test import override_settings
from django.utils import timezone

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.domains.workbasket.app_data import (
    _add_user_import_annotations,
    _get_open_case_emails_annotation,
    _get_open_firs_pk_annotation,
)
from web.domains.workbasket.base import WorkbasketSection
from web.domains.workbasket.row import get_workbasket_row_func
from web.models import (
    FurtherInformationRequest,
    ImportApplicationType,
    Task,
    UpdateRequest,
    WithdrawApplication,
    WoodQuotaApplication,
)


@pytest.fixture
def app_in_progress(db, importer, importer_one_contact):
    app = _create_wood_app(importer, importer_one_contact, ImpExpStatus.IN_PROGRESS)
    return _get_wood_app_with_annotations(app)


@pytest.fixture
def app_submitted(db, importer, importer_one_contact):
    app = _create_wood_app(importer, importer_one_contact, ImpExpStatus.SUBMITTED)
    app.submit_datetime = timezone.now()
    app.save()
    return _get_wood_app_with_annotations(app)


@pytest.fixture
def app_processing(db, importer, importer_one_contact, ilb_admin_user):
    app = _create_wood_app(
        importer,
        importer_one_contact,
        ImpExpStatus.PROCESSING,
        case_owner=ilb_admin_user,
    )

    Task.objects.create(process=app, task_type=Task.TaskType.PROCESS)

    return _get_wood_app_with_annotations(app)


@pytest.fixture
def app_completed(db, importer, importer_one_contact):
    app = _create_wood_app(importer, importer_one_contact, ImpExpStatus.COMPLETED)
    return _get_wood_app_with_annotations(app)


@pytest.fixture
def app_completed_agent(db, importer, importer_one_agent_one_contact, agent_importer):
    app = _create_wood_app(
        importer, importer_one_agent_one_contact, ImpExpStatus.COMPLETED, agent=agent_importer
    )
    return _get_wood_app_with_annotations(app)


def test_actions_in_progress(app_in_progress, importer_one_contact):
    get_row = get_workbasket_row_func(app_in_progress.process_type)
    user_row = get_row(app_in_progress, importer_one_contact, False)

    assert user_row.timestamp == app_in_progress.created

    _check_actions(user_row.sections, expected_actions={"Resume", "Cancel"})


def test_actions_submitted(app_submitted, importer_one_contact):
    get_row = get_workbasket_row_func(app_submitted.process_type)

    user_row = get_row(app_submitted, importer_one_contact, False)

    assert user_row.timestamp == app_submitted.submit_datetime

    _check_actions(user_row.sections, expected_actions={"Withdraw", "View Application"})


def test_actions_processing(app_processing, importer_one_contact):
    get_row = get_workbasket_row_func(app_processing.process_type)
    user_row = get_row(app_processing, importer_one_contact, False)

    _check_actions(user_row.sections, expected_actions={"Withdraw", "View Application"})


def test_actions_fir_withdrawal_update_request(app_processing, importer_one_contact):
    # fetch the app to refresh the annotations after creating a fir withdrawal
    _create_fir_withdrawal(app_processing, importer_one_contact)
    app_processing = _get_wood_app_with_annotations(app_processing)

    get_row = get_workbasket_row_func(app_processing.process_type)
    user_row = get_row(app_processing, importer_one_contact, False)
    _check_actions(
        user_row.sections,
        expected_actions={"Pending Withdrawal", "View Application", "Respond"},
    )

    _create_update_request(app_processing)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    user_row = get_row(app_processing, importer_one_contact, False)

    _check_actions(
        user_row.sections,
        expected_actions={
            "Pending Withdrawal",
            "View Application",
            "Respond",
            "Respond to Update Request",
        },
    )


def test_actions_authorise(app_processing, importer_one_contact):
    _update_task(app_processing, Task.TaskType.AUTHORISE)
    get_row = get_workbasket_row_func(app_processing.process_type)
    user_row = get_row(app_processing, importer_one_contact, False)

    _check_actions(user_row.sections, expected_actions={"Withdraw", "View Application"})


def test_actions_bypass_chief(app_processing, importer_one_contact):
    _update_task(app_processing, Task.TaskType.CHIEF_WAIT)
    get_row = get_workbasket_row_func(app_processing.process_type)

    user_row = get_row(app_processing, importer_one_contact, False)

    _check_actions(user_row.sections, expected_actions={"Withdraw", "View Application"})

    _update_task(app_processing, Task.TaskType.CHIEF_ERROR)
    user_row = get_row(app_processing, importer_one_contact, False)

    _check_actions(user_row.sections, expected_actions={"Withdraw", "View Application"})


def test_actions_completed(app_completed, importer_one_contact):
    get_row = get_workbasket_row_func(app_completed.process_type)
    user_row = get_row(app_completed, importer_one_contact, False)

    _check_actions(
        user_row.sections,
        expected_actions={"View Application", "Clear"},
    )


def test_admin_actions_in_progress_ilb_admin(app_in_progress, ilb_admin_user):
    get_row = get_workbasket_row_func(app_in_progress.process_type)
    admin_row = get_row(app_in_progress, ilb_admin_user, True)

    assert admin_row.sections == []


def test_admin_actions_submitted(app_submitted, ilb_admin_user):
    get_row = get_workbasket_row_func(app_submitted.process_type)
    admin_row = get_row(app_submitted, ilb_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Take Ownership", "View"})

    _test_view_endpoint_is_case_management(app_submitted, admin_row.sections)


def test_admin_actions_processing(app_processing, ilb_admin_user):
    get_row = get_workbasket_row_func(app_processing.process_type)
    admin_row = get_row(app_processing, ilb_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Manage"})


def test_admin_actions_fir_withdrawal_update_request(
    app_processing, importer_one_contact, ilb_admin_user
):
    _create_fir_withdrawal(app_processing, importer_one_contact)
    get_row = get_workbasket_row_func(app_processing.process_type)
    admin_row = get_row(app_processing, ilb_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Manage"})

    _create_update_request(app_processing)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    admin_row = get_row(app_processing, ilb_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Manage"})
    section = admin_row.sections[0]
    assert (
        section.information
        == "Application Processing, Out for Update, Further Information Requested"
    )


def test_admin_actions_authorise(app_processing, ilb_admin_user):
    _update_task(app_processing, Task.TaskType.AUTHORISE)

    get_row = get_workbasket_row_func(app_processing.process_type)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    admin_row = get_row(app_processing, ilb_admin_user, True)

    _check_actions(
        admin_row.sections,
        expected_actions={"Cancel Authorisation", "Authorise Documents", "View Case"},
    )

    _test_view_endpoint_is_case_management(app_processing, admin_row.sections, "View Case")


@override_settings(ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD=True)
def test_admin_actions_bypass_chief(app_processing, ilb_admin_user):
    _update_task(app_processing, Task.TaskType.CHIEF_WAIT)
    get_row = get_workbasket_row_func(app_processing.process_type)
    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    admin_row = get_row(app_processing, ilb_admin_user, True)

    _check_actions(
        admin_row.sections,
        expected_actions={
            "(TEST) Bypass CHIEF induce failure",
            "(TEST) Bypass CHIEF",
            "Monitor Progress",
            "View Case",
        },
    )

    _test_view_endpoint_is_case_management(app_processing, admin_row.sections, "View Case")

    _update_task(app_processing, Task.TaskType.CHIEF_ERROR)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    admin_row = get_row(app_processing, ilb_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Show Licence Details", "View"})
    _test_view_endpoint_is_case_management(app_processing, admin_row.sections)


@override_settings(ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD=True, SEND_LICENCE_TO_CHIEF=True)
def test_admin_actions_bypass_chief_disabled_when_sending_to_chief(app_processing, ilb_admin_user):
    _update_task(app_processing, Task.TaskType.CHIEF_WAIT)

    get_row = get_workbasket_row_func(app_processing.process_type)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    admin_row = get_row(app_processing, ilb_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Monitor Progress", "View Case"})

    _test_view_endpoint_is_case_management(app_processing, admin_row.sections, "View Case")

    _update_task(app_processing, Task.TaskType.CHIEF_ERROR)

    # fetch the app again as we've updated the tasks
    app_processing = _get_wood_app_with_annotations(app_processing)

    admin_row = get_row(app_processing, ilb_admin_user, True)

    _check_actions(admin_row.sections, expected_actions={"Show Licence Details", "View"})
    _test_view_endpoint_is_case_management(app_processing, admin_row.sections)


def test_admin_actions_completed(app_completed, ilb_admin_user):
    get_row = get_workbasket_row_func(app_completed.process_type)
    admin_row = get_row(app_completed, ilb_admin_user, True)

    # By default the admin shouldn't see anything
    assert len(admin_row.sections) == 0

    # Reject an application to see admin "Completed" actions
    app_completed.case_owner = ilb_admin_user
    app_completed.save()
    Task.objects.create(process=app_completed, task_type=Task.TaskType.REJECTED, previous=None)

    # Need to override the active_tasks annotation now we have updated it.
    app_completed.active_tasks = case_progress.get_active_task_list(app_completed)

    admin_row = get_row(app_completed, ilb_admin_user, True)
    _check_actions(admin_row.sections, expected_actions={"View Case"})


def _check_actions(sections: list[WorkbasketSection], expected_actions: set[str]):
    """Combine all the actions in each section and test equal to the expected actions"""
    all_actions = set()

    for section in sections:
        actions = section.actions
        row_actions = {r.name for r in actions}
        all_actions.update(row_actions)

    assert all_actions == expected_actions


def _create_fir_withdrawal(app, importer_one_contact):
    app.further_information_requests.create(
        process_type=FurtherInformationRequest.PROCESS_TYPE, status=FurtherInformationRequest.OPEN
    )

    app.withdrawals.create(
        status=WithdrawApplication.Statuses.OPEN, request_by=importer_one_contact
    )


def _create_update_request(app):
    app.update_requests.create(status=UpdateRequest.Status.OPEN)
    _update_task(app, Task.TaskType.PREPARE)


def _update_task(app, new_task_type):
    task = case_progress.get_active_tasks(app).first()
    task.is_active = False
    task.save()
    Task.objects.create(process=app, task_type=new_task_type, previous=task)


def _create_wood_app(importer, importer_one_contact, status, agent=None, case_owner=None):
    return WoodQuotaApplication.objects.create(
        process_type=WoodQuotaApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.WOOD_QUOTA
        ),
        importer=importer,
        agent=agent,
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
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
    app = _add_user_import_annotations(WoodQuotaApplication.objects.filter(pk=app.pk))

    open_fir_pks_annotation = _get_open_firs_pk_annotation("further_information_requests")
    app = app.annotate(
        annotation_open_fir_pks=open_fir_pks_annotation,
        open_case_emails=_get_open_case_emails_annotation("import_applications"),
    )

    return app.get()
