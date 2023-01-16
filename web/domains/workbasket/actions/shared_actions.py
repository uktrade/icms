from web.domains.case.shared import ImpExpStatus
from web.domains.workbasket.base import WorkbasketAction

from .base import Action, ActionT

"""Actions that apply to both ilb admin and importer/exporter users are added here"""


class ClearApplicationAction(Action):
    """Action used by applicant / admin to clear an application row."""

    def show_link(self) -> bool:
        show_link = False

        if self.is_ilb_admin:
            if self.is_rejected and self.is_case_owner():
                show_link = True

        else:
            if self.status == ImpExpStatus.COMPLETED:
                show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        if self.is_ilb_admin:
            section_label = "View Case"
        else:
            section_label = "Application View"

        # ICMSLST-19 Add clear action
        return [WorkbasketAction(is_post=False, name="Clear", url="#", section_label=section_label)]


SHARED_ACTIONS: list[ActionT] = [
    ClearApplicationAction,
]
