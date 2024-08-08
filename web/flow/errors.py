from typing import Any

from django.core.exceptions import PermissionDenied

from web.domains.case.shared import ImpExpStatus
from web.models import Task


class ProcessError(PermissionDenied): ...  # noqa: E701


class ProcessInactiveError(ProcessError): ...  # noqa: E701


class ProcessStatusError(ProcessError):
    app_status: ImpExpStatus

    def __init__(self, *args: Any, app_status: ImpExpStatus, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.app_status = app_status


class TaskError(ProcessError):
    def __init__(
        self, *args: Any, app_status: ImpExpStatus, task: Task.TaskType, **kwargs: Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.app_status = app_status
        self.expected_task = task
