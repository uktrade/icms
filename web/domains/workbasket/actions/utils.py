from collections import defaultdict

from web.domains.case.types import ImpOrExp
from web.domains.workbasket.base import WorkbasketSection
from web.models import User

from .applicant_actions import APPLICANT_ACTIONS
from .base import ActionConfig, ActionT
from .ilb_admin_actions import CASEWORKER_ACTIONS


def get_workbasket_admin_sections(
    user: User, case_type: str, application: ImpOrExp
) -> list[WorkbasketSection]:
    """Returns all admin actions that should be shown for this application."""

    return _get_workbasket_sections(user, case_type, application, CASEWORKER_ACTIONS)


def get_workbasket_applicant_sections(
    user: User, case_type: str, application: ImpOrExp
) -> list[WorkbasketSection]:
    """Returns all applicant actions that should be shown for this application."""

    return _get_workbasket_sections(user, case_type, application, APPLICANT_ACTIONS)


def _get_workbasket_sections(
    user: User, case_type: str, application: ImpOrExp, workbasket_actions: list[ActionT]
) -> list[WorkbasketSection]:
    # Group all actions by the label.
    sections = defaultdict(list)

    config = ActionConfig(user=user, case_type=case_type, application=application)

    for action_cls in workbasket_actions:
        action = action_cls.from_config(config)

        if action.show_link():
            for wb_action in action.get_workbasket_actions():
                group = wb_action.section_label or "Unknown information - please report this bug"
                sections[group].append(wb_action)

    return [
        WorkbasketSection(information=label, actions=actions) for label, actions in sections.items()
    ]
