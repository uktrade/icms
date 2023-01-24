from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import QuerySet

from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp  # , ImpOrExpOrAccess
from web.flow import errors
from web.flow.models import Process, Task

TT = Task.TaskType
ST = ImpExpStatus

__all__ = [
    #
    # Functions to check an application is at a particular point in the application process
    #
    "application_in_progress",
    #
    # Utility functions
    #
    "check_expected_status",
    "check_expected_task",
    "get_expected_task",
    "get_active_tasks",
    "get_active_task_list",
]


def application_in_progress(application: ImpOrExp) -> None:
    """Check if the application is in progress with the applicant."""

    # A fresh new application (IN_PROGRESS)
    # An update request (PROCESSING / VARIATION_REQUESTED)
    expected_status = [ST.IN_PROGRESS, ST.PROCESSING, ST.VARIATION_REQUESTED]
    expected_task = Task.TaskType.PREPARE

    check_expected_status(application, expected_status)
    check_expected_task(application, expected_task)


def check_expected_status(application: Process, expected_statuses: list[str]) -> None:
    """Check the process has one of the expected statuses."""

    # status is set as a model field on all derived classes
    status: str = application.status  # type: ignore[attr-defined]

    if status not in expected_statuses:
        raise errors.ProcessStateError(f"Process is in the wrong state: {status}")


def check_expected_task(application: ImpOrExp, expected_task: str) -> None:
    """Check the expected task is in the applications active task list"""

    active_tasks = get_active_task_list(application)

    if expected_task not in active_tasks:
        raise errors.TaskError(
            f"{expected_task} not in active task list {active_tasks} for process {application.reference}"
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


def get_active_tasks(application: Process, select_for_update=True) -> QuerySet[Task]:
    """Get all active task for current process."""

    tasks = application.tasks.filter(is_active=True)

    return tasks.select_for_update() if select_for_update else tasks


def get_active_task_list(application: Process) -> list[str]:
    return list(get_active_tasks(application, False).values_list("task_type", flat=True))
