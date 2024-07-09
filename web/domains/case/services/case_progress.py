from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import QuerySet

from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.domains.case.views.mixins import ApplicationTaskMixin
from web.flow import errors
from web.models import AccessRequest, ApprovalRequest, Process, Task

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
    #
    # View Mixins
    #
    "InProgressApplicationStatusTaskMixin",
]


# Consider splitting to the following if required in the future:
#   - def application_in_progress
#   - def application_in_progress_update_request
#   - def application_in_progress_variation_request
def application_in_progress(application: ImpOrExp) -> None:
    """Check if the application is in progress with the applicant."""

    # A fresh new application (IN_PROGRESS)
    # An update request (PROCESSING / VARIATION_REQUESTED)
    expected_status = [ST.IN_PROGRESS, ST.PROCESSING, ST.VARIATION_REQUESTED]
    expected_task = TT.PREPARE

    try:
        check_expected_status(application, expected_status)
    except errors.ProcessStateError as e:
        # Special case where a case officer creates an update request and then releases ownership.
        # Release ownership will change the status to SUBMITTED and therefore the
        # check_expected_status call will raise an exception.
        if not (
            application.status == ST.SUBMITTED
            and not application.case_owner
            and application.current_update_requests().exists()
        ):
            raise e

    check_expected_task(application, expected_task)


class InProgressApplicationStatusTaskMixin(ApplicationTaskMixin):
    """Mixin for class based views that is equivalent to case_progress.application_in_progress()"""

    current_status = [ST.IN_PROGRESS, ST.PROCESSING, ST.VARIATION_REQUESTED]
    current_task_type = TT.PREPARE

    def has_object_permission(self) -> bool:
        """Mandatory user object permission checking for the loaded `self.application` record."""
        raise NotImplementedError("has_object_permission must be implemented.")


def application_in_processing(application: ImpOrExp) -> None:
    """Check if an application is being processed by a caseworker."""

    expected_status = [ST.SUBMITTED, ST.PROCESSING, ST.VARIATION_REQUESTED]
    expected_task = TT.PROCESS

    check_expected_status(application, expected_status)
    check_expected_task(application, expected_task)


def access_request_in_processing(application: AccessRequest) -> None:
    """Check if an access request is being processed by a caseworker"""

    expected_status = [AccessRequest.Statuses.SUBMITTED]
    expected_task = TT.PROCESS

    check_expected_status(application, expected_status)  # type:ignore[arg-type]
    check_expected_task(application, expected_task)


def approval_request_in_processing(application: ApprovalRequest) -> None:
    expected_status = [ApprovalRequest.Statuses.OPEN]

    check_expected_status(application, expected_status)  # type:ignore[arg-type]


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


def check_expected_status(application: Process, expected_statuses: list[ImpExpStatus]) -> None:
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


def get_expected_task(
    application: Process, task_type: str, *, select_for_update: bool = True
) -> Task:
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


def get_active_tasks(application: Process, select_for_update: bool = True) -> QuerySet[Task]:
    """Get all active task for current process."""

    tasks = application.tasks.filter(is_active=True)

    return tasks.select_for_update() if select_for_update else tasks
