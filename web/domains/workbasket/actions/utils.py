from collections import defaultdict
from typing import TYPE_CHECKING

from web.domains.case.shared import ImpExpStatus
from web.domains.workbasket.base import WorkbasketSection
from web.models import Task
from web.permissions import Perms

from .applicant_actions import REQUEST_VARIATION_APPLICANT_ACTIONS
from .ilb_admin_actions import ILB_ADMIN_ACTIONS
from .shared_actions import SHARED_ACTIONS

if TYPE_CHECKING:
    from web.domains.case.types import ImpOrExp
    from web.models import User

    from .base import ActionT


def get_workbasket_admin_sections(
    user: "User", case_type: str, application: "ImpOrExp"
) -> list[WorkbasketSection]:
    """Returns all admin actions that should be shown for this application."""

    actions = ILB_ADMIN_ACTIONS + SHARED_ACTIONS

    return _get_workbasket_sections(user, case_type, application, actions)


def get_workbasket_applicant_sections(
    user: "User", case_type: str, application: "ImpOrExp"
) -> list[WorkbasketSection]:
    """Returns all applicant actions that should be shown for this application."""

    actions = REQUEST_VARIATION_APPLICANT_ACTIONS + SHARED_ACTIONS

    return _get_workbasket_sections(user, case_type, application, actions)


def _get_workbasket_sections(
    user: "User", case_type: str, application: "ImpOrExp", workbasket_actions: list["ActionT"]
) -> list[WorkbasketSection]:
    # This is an annotation of all the active tasks linked to this application
    tasks = application.active_tasks

    is_ilb_admin = user.has_perm(Perms.sys.ilb_admin)
    is_importer_user = user.has_perm("web.importer_access")

    # Group all actions by the label.
    sections = defaultdict(list)

    for action_cls in workbasket_actions:
        action = action_cls(
            user=user,
            case_type=case_type,
            application=application,
            tasks=tasks,
            is_ilb_admin=is_ilb_admin,
            is_importer_user=is_importer_user,
            is_rejected=_is_rejected(application, tasks),
        )

        if action.show_link():
            for wb_action in action.get_workbasket_actions():
                group = wb_action.section_label or "Unknown information - please report this bug"
                sections[group].append(wb_action)

    return [
        WorkbasketSection(information=label, actions=actions) for label, actions in sections.items()
    ]


def _is_rejected(application: "ImpOrExp", active_tasks: list[str]) -> bool:
    """Is the application in a rejected state."""

    return application.status == ImpExpStatus.COMPLETED and Task.TaskType.REJECTED in active_tasks
