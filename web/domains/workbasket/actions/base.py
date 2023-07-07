import dataclasses
from typing import Any, Self

from web.domains.case.types import ImpOrExp
from web.domains.workbasket.base import WorkbasketAction
from web.models import Task, User
from web.permissions import AppChecker


@dataclasses.dataclass
class ActionConfig:
    """Cache shared between all actions."""

    user: User
    case_type: str
    application: ImpOrExp
    tasks: list[str] = dataclasses.field(init=False)
    app_checker: AppChecker = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        # This is an annotation of all the active tasks linked to this application
        self.tasks = self.application.active_tasks
        # Cached app checker to share between all actions.
        self.app_checker = AppChecker(self.user, self.application)


class Action:
    """Base class for all actions.

    Determines if an action should be shown in the workbasket.
    """

    def __init__(
        self,
        user: User,
        case_type: str,
        application: ImpOrExp,
        tasks: list[str],
        app_checker: AppChecker,
    ) -> None:
        self.user = user
        self.case_type = case_type
        self.application = application
        self.active_tasks = tasks
        self.status = self.application.status
        self.app_checker = app_checker

    @classmethod
    def from_config(cls, config: ActionConfig) -> Self:
        return cls(
            user=config.user,
            case_type=config.case_type,
            application=config.application,
            tasks=config.tasks,
            app_checker=config.app_checker,
        )

    def show_link(self) -> bool:
        raise NotImplementedError

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        raise NotImplementedError

    def is_case_owner(self) -> bool:
        return self.application.case_owner == self.user

    def get_kwargs(self) -> dict[str, Any]:
        return {"application_pk": self.application.pk, "case_type": self.case_type}

    def has_task(self, *tasks: Task.TaskType) -> bool:
        """Return true if any of the supplied tasks are in the active task list.

        :param tasks: Tasks to check
        """

        for task in tasks:
            if task in self.active_tasks:
                return True

        return False


ActionT = type[Action]
