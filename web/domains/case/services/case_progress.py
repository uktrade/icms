from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import QuerySet

from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.flow import errors
from web.models import AccessRequest, Process, Task

TT = Task.TaskType
ST = ImpExpStatus

__all__ = [
    #
    # Functions to check an application is at a particular point in the application process
    #
    "application_in_progress",
    "application_in_processing",
    "access_request_in_processing",
    "application_is_authorised",
    "application_is_with_chief",
    #
    # Utility functions
    #
    "check_expected_status",
    "check_expected_task",
    "get_expected_task",
    "get_active_tasks",
    "get_active_task_list",
]


# TODO: Consider splitting.
#       def application_in_progress
#       def application_in_progress_update_request
#       def application_in_progress_variation_request
def application_in_progress(application: ImpOrExp) -> None:
    """Check if the application is in progress with the applicant."""

    # A fresh new application (IN_PROGRESS)
    # An update request (PROCESSING / VARIATION_REQUESTED)
    expected_status = [ST.IN_PROGRESS, ST.PROCESSING, ST.VARIATION_REQUESTED]
    expected_task = TT.PREPARE

    check_expected_status(application, expected_status)
    check_expected_task(application, expected_task)


def application_in_processing(application: ImpOrExp) -> None:
    """Check if an application is being processed by a caseworker."""

    expected_status = [ST.SUBMITTED, ST.PROCESSING, ST.VARIATION_REQUESTED]
    expected_task = TT.PROCESS

    check_expected_status(application, expected_status)
    check_expected_task(application, expected_task)


def access_request_in_processing(application: AccessRequest) -> None:
    """Check if an access request is being processed by a caseworker"""

    expected_status = [ST.SUBMITTED]
    expected_task = TT.PROCESS

    check_expected_status(application, expected_status)
    check_expected_task(application, expected_task)


def application_is_authorised(application: ImpOrExp) -> None:
    """Check if an application has been authorised."""

    expected_status = [ST.PROCESSING, ST.VARIATION_REQUESTED]
    expected_task = TT.AUTHORISE

    check_expected_status(application, expected_status)
    check_expected_task(application, expected_task)


def application_is_with_chief(application: ImpOrExp) -> None:
    """Check if an application is with CHIEF."""

    expected_status = [ST.PROCESSING, ST.VARIATION_REQUESTED]
    expected_task = TT.CHIEF_WAIT

    check_expected_status(application, expected_status)
    check_expected_task(application, expected_task)


def check_expected_status(application: Process, expected_statuses: list[str]) -> None:
    """Check the process has one of the expected statuses."""

    # status is set as a model field on all derived classes
    status: str = application.status

    if status not in expected_statuses:
        raise errors.ProcessStateError(f"Process is in the wrong state: {status}")


def check_expected_task(application: Process, expected_task: str) -> None:
    """Check the expected task is in the applications active task list"""

    active_tasks = get_active_task_list(application)

    if expected_task not in active_tasks:
        raise errors.TaskError(
            f"{expected_task} not in active task list {active_tasks} for Process {application.pk}"
        )


def get_expected_task(application: Process, task_type: str, *, select_for_update=True) -> Task:
    """Get the expected active current task"""

    if not application.is_active:
        raise errors.ProcessInactiveError("Process is not active")

    try:
        task = get_active_tasks(application, select_for_update).get(task_type=task_type)

    except (ObjectDoesNotExist, MultipleObjectsReturned) as exc:
        raise errors.TaskError(f"Failed to get expected task: {task_type}") from exc

    return task


def get_active_task_list(application: Process) -> list[str]:
    """Get all active tasks for the current process as a list"""

    return list(get_active_tasks(application, False).values_list("task_type", flat=True))


def get_active_tasks(application: Process, select_for_update=True) -> QuerySet[Task]:
    """Get all active task for current process."""

    tasks = application.tasks.filter(is_active=True)

    return tasks.select_for_update() if select_for_update else tasks
