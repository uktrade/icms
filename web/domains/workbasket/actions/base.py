from typing import TYPE_CHECKING, Any

from web.domains.workbasket.base import WorkbasketAction

if TYPE_CHECKING:
    from web.domains.case.types import ImpOrExp
    from web.domains.user.models import User


class Action:
    """Base class for all actions.

    Determines if an action should be shown in the workbasket.
    """

    def __init__(
        self,
        user: "User",
        case_type: str,
        application: "ImpOrExp",
        tasks: list[str],
        is_ilb_admin: bool,
        is_importer_user: bool,
    ) -> None:
        self.user = user
        self.case_type = case_type
        self.application = application
        self.active_tasks = tasks
        self.status = self.application.status
        self.is_ilb_admin = is_ilb_admin
        self.is_importer_user = is_importer_user

    def show_link(self) -> bool:
        raise NotImplementedError

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        raise NotImplementedError

    def is_case_owner(self) -> bool:
        return self.application.case_owner == self.user

    def get_kwargs(self) -> dict[str, Any]:
        return {"application_pk": self.application.pk, "case_type": self.case_type}


ActionT = type[Action]
