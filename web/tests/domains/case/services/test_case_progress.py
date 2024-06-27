import pytest

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.flow import errors
from web.models import Task, UpdateRequest

TT = Task.TaskType
ST = ImpExpStatus


def test_application_in_progress(fa_sil):
    _setup_application(fa_sil, ST.IN_PROGRESS, TT.PREPARE)
    case_progress.application_in_progress(fa_sil)

    with pytest.raises(errors.ProcessStateError):
        _setup_application(fa_sil, ST.COMPLETED, TT.PREPARE)
        case_progress.application_in_progress(fa_sil)

    with pytest.raises(errors.TaskError):
        _setup_application(fa_sil, ST.IN_PROGRESS, TT.REJECTED)
        case_progress.application_in_progress(fa_sil)


def test_application_in_progress_update_request(fa_sil, ilb_admin_user):
    # Test edge case where a case officer creates an update request
    _setup_application(fa_sil, ST.PROCESSING, TT.PREPARE)
    fa_sil.case_owner = ilb_admin_user
    fa_sil.save()

    fa_sil.update_requests.create(status=UpdateRequest.Status.OPEN)
    case_progress.application_in_progress(fa_sil)


def test_application_in_progress_update_request_no_case_owner(fa_sil, ilb_admin_user):
    # edge case where a case officer creates an update request and then releases ownership of
    # the case.
    _setup_application(fa_sil, ST.SUBMITTED, TT.PREPARE)
    fa_sil.case_owner = None
    fa_sil.save()

    fa_sil.update_requests.create(status=UpdateRequest.Status.OPEN)
    case_progress.application_in_progress(fa_sil)

    # if the case officer is set it is incorrect.
    with pytest.raises(errors.ProcessStateError):
        fa_sil.case_owner = ilb_admin_user
        fa_sil.save()
        case_progress.application_in_progress(fa_sil)

    # If submitted without an update request it is incorrect
    with pytest.raises(errors.ProcessStateError):
        fa_sil.case_owner = None
        fa_sil.save()
        fa_sil.current_update_requests().delete()
        case_progress.application_in_progress(fa_sil)


def test_application_in_processing(fa_sil):
    _setup_application(fa_sil, ST.PROCESSING, TT.PROCESS)
    case_progress.application_in_processing(fa_sil)

    with pytest.raises(errors.ProcessStateError):
        _setup_application(fa_sil, ST.COMPLETED, TT.PROCESS)
        case_progress.application_in_processing(fa_sil)

    with pytest.raises(errors.TaskError):
        _setup_application(fa_sil, ST.PROCESSING, TT.REJECTED)
        case_progress.application_in_processing(fa_sil)


def test_access_request_in_processing(iar):
    _setup_application(iar, ST.SUBMITTED, TT.PROCESS)
    case_progress.access_request_in_processing(iar)

    with pytest.raises(errors.ProcessStateError):
        _setup_application(iar, ST.COMPLETED, TT.PROCESS)
        case_progress.access_request_in_processing(iar)

    with pytest.raises(errors.TaskError):
        _setup_application(iar, ST.SUBMITTED, TT.REJECTED)
        case_progress.access_request_in_processing(iar)


def test_application_is_authorised(fa_sil):
    _setup_application(fa_sil, ST.VARIATION_REQUESTED, TT.AUTHORISE)
    case_progress.application_is_authorised(fa_sil)

    with pytest.raises(errors.ProcessStateError):
        _setup_application(fa_sil, ST.COMPLETED, TT.AUTHORISE)
        case_progress.application_is_authorised(fa_sil)

    with pytest.raises(errors.TaskError):
        _setup_application(fa_sil, ST.VARIATION_REQUESTED, TT.REJECTED)
        case_progress.application_is_authorised(fa_sil)


def test_application_is_with_chief(fa_sil):
    _setup_application(fa_sil, ST.PROCESSING, TT.CHIEF_WAIT)
    case_progress.application_is_with_chief(fa_sil)

    with pytest.raises(errors.ProcessStateError):
        _setup_application(fa_sil, ST.COMPLETED, TT.CHIEF_WAIT)
        case_progress.application_is_with_chief(fa_sil)

    with pytest.raises(errors.TaskError):
        _setup_application(fa_sil, ST.PROCESSING, TT.REJECTED)
        case_progress.application_is_with_chief(fa_sil)


def test_check_expected_status(fa_sil):
    fa_sil.status = ST.COMPLETED
    expected_statuses = [ST.COMPLETED]
    case_progress.check_expected_status(fa_sil, expected_statuses)

    with pytest.raises(errors.ProcessStateError):
        fa_sil.status = ST.REVOKED
        case_progress.check_expected_status(fa_sil, expected_statuses)


def test_check_expected_task(fa_sil):
    _setup_application(fa_sil, ST.PROCESSING, TT.CHIEF_WAIT)

    case_progress.check_expected_task(fa_sil, TT.CHIEF_WAIT)

    with pytest.raises(errors.TaskError):
        case_progress.check_expected_task(fa_sil, TT.CHIEF_ERROR)


def test_get_expected_task(fa_sil):
    _setup_application(fa_sil, ST.PROCESSING, TT.CHIEF_WAIT)

    task = case_progress.get_expected_task(fa_sil, TT.CHIEF_WAIT)
    assert task.task_type == TT.CHIEF_WAIT

    with pytest.raises(errors.TaskError):
        case_progress.get_expected_task(fa_sil, TT.PREPARE)

    fa_sil.is_active = False
    with pytest.raises(errors.ProcessInactiveError):
        case_progress.get_expected_task(fa_sil, TT.CHIEF_WAIT)


def test_get_active_tasks(fa_sil):
    # A fake old task that is inactive
    Task.objects.create(process=fa_sil, task_type=TT.VR_REQUEST_CHANGE, is_active=False)

    # An app going through a variation request that has a request for changes from the applicant.
    _setup_application(fa_sil, ST.VARIATION_REQUESTED, TT.PROCESS)
    Task.objects.create(process=fa_sil, task_type=TT.VR_REQUEST_CHANGE)

    tasks = case_progress.get_active_tasks(fa_sil)
    assert tasks.count() == 2
    tasks.get(task_type=TT.PROCESS)
    tasks.get(task_type=TT.VR_REQUEST_CHANGE)


def test_get_active_task_list(fa_sil):
    # A fake old task that is inactive
    Task.objects.create(process=fa_sil, task_type=TT.VR_REQUEST_CHANGE, is_active=False)

    # An app going through a variation request that has a request for changes from the applicant.
    _setup_application(fa_sil, ST.VARIATION_REQUESTED, TT.PROCESS)
    Task.objects.create(process=fa_sil, task_type=TT.VR_REQUEST_CHANGE)

    tasks = case_progress.get_active_task_list(fa_sil)
    assert len(tasks) == 2

    assert TT.PROCESS in tasks
    assert TT.VR_REQUEST_CHANGE in tasks


def _setup_application(application: ImpOrExp, status, task_type) -> None:
    """Helper function to fake an application in to a particular status"""

    # Set the new status
    application.status = status
    application.save()

    # Get rid of any other tasks
    old_tasks = case_progress.get_active_tasks(application, select_for_update=True)
    old_tasks.update(is_active=False)

    # Create the new task
    Task.objects.create(process=application, task_type=task_type)
