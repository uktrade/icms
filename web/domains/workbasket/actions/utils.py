from typing import TYPE_CHECKING

from web.domains.workbasket.base import WorkbasketAction

from .applicant_actions import REQUEST_VARIATION_APPLICANT_ACTIONS
from .ilb_admin_actions import ILB_ADMIN_ACTIONS
from .shared_actions import SHARED_ACTIONS

if TYPE_CHECKING:
    from web.domains.case.types import ImpOrExp
    from web.domains.user.models import User

    from .base import ActionT


def get_workbasket_actions(
    user: "User", case_type: str, application: "ImpOrExp"
) -> list[WorkbasketAction]:
    """Returns all admin actions that should be shown for this application."""

    actions = ILB_ADMIN_ACTIONS + SHARED_ACTIONS

    return _get_workbasket_actions(user, case_type, application, actions)


def get_workbasket_applicant_actions(
    user: "User", case_type: str, application: "ImpOrExp"
) -> list[WorkbasketAction]:
    """Returns all applicant actions that should be shown for this application."""

    actions = REQUEST_VARIATION_APPLICANT_ACTIONS + SHARED_ACTIONS

    return _get_workbasket_actions(user, case_type, application, actions)


def _get_workbasket_actions(
    user: "User", case_type: str, application: "ImpOrExp", workbasket_actions: list["ActionT"]
) -> list[WorkbasketAction]:
    tasks = application.get_active_task_list()

    wb_actions: list[WorkbasketAction] = []

    is_ilb_admin = user.has_perm("web.ilb_admin")
    is_importer_user = user.has_perm("web.importer_access")

    for action_cls in workbasket_actions:
        action = action_cls(
            user=user,
            case_type=case_type,
            application=application,
            tasks=tasks,
            is_ilb_admin=is_ilb_admin,
            is_importer_user=is_importer_user,
        )

        if action.show_link():
            wb_actions.extend(action.get_workbasket_actions())

    return wb_actions
