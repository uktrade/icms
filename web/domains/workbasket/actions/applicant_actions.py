from typing import TYPE_CHECKING, Any, Optional

from django.urls import reverse

from web.domains.case.shared import ImpExpStatus
from web.domains.workbasket.base import WorkbasketAction
from web.flow.models import ProcessTypes, Task

from .base import Action, ActionT

if TYPE_CHECKING:
    from web.domains.case._import.fa.models import SupplementaryInfoBase

"""Actions that only apply to importer/exporter users are added here"""


class EditApplicationAction(Action):
    """Applicant action to resume editing the application"""

    def show_link(self) -> bool:
        show_link = False

        if self.status == ImpExpStatus.IN_PROGRESS:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        return [
            WorkbasketAction(
                is_post=False,
                name="Resume",
                url=reverse(
                    self.application.get_edit_view_name(),
                    kwargs={"application_pk": self.application.pk},
                ),
                section_label="Prepare Application",
            )
        ]


class CancelApplicationAction(Action):
    """Applicant action to resume editing the application"""

    def show_link(self) -> bool:
        show_link = False

        if self.status == ImpExpStatus.IN_PROGRESS:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=True,
                name="Cancel",
                url=reverse("case:cancel", kwargs=kwargs),
                confirm="Are you sure you want to cancel this draft application? All entered data will be lost.",
                section_label="Prepare Application",
            )
        ]


class ViewApplicationAction(Action):
    """Applicant action to view the application"""

    def show_link(self) -> bool:
        show_link = False

        valid_statuses = [
            ImpExpStatus.SUBMITTED,
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
            ImpExpStatus.COMPLETED,
        ]

        if self.status in valid_statuses:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        sections = {
            ImpExpStatus.SUBMITTED: "Application Submitted",
            ImpExpStatus.PROCESSING: "Application Submitted",
            ImpExpStatus.VARIATION_REQUESTED: "Application Submitted",
            ImpExpStatus.COMPLETED: "Application View",
        }

        return [
            WorkbasketAction(
                is_post=False,
                name="View Application",
                url=reverse("case:view", kwargs=kwargs),
                section_label=sections[self.status],
            )
        ]


class RespondToFurtherInformationRequestAction(Action):
    def show_link(self) -> bool:
        correct_status = self.status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        open_firs = self.application.further_information_requests.open()

        return correct_status and open_firs.exists()

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()
        open_firs = self.application.further_information_requests.open()

        return [
            WorkbasketAction(
                is_post=False,
                name="Respond",
                url=reverse("case:respond-fir", kwargs=kwargs | {"fir_pk": fir.pk}),
                section_label=f"Further Information Request, {fir.requested_datetime.strftime('%d %b %Y %H:%M:%S')}",
            )
            for fir in open_firs.order_by("requested_datetime")
        ]


class RespondToUpdateRequestAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        correct_task = Task.TaskType.PREPARE in self.active_tasks
        open_requests = self.application.current_update_requests().filter(status="OPEN")

        if correct_status and correct_task and open_requests.exists():
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()
        open_requests = self.application.current_update_requests().filter(status="OPEN")

        # TODO: There *should* only ever be a single "Respond to Update Request" link
        return [
            WorkbasketAction(
                is_post=False,
                name="Respond to Update Request",
                url=reverse(
                    "case:start-update-request",
                    kwargs=kwargs | {"update_request_pk": update.pk},
                ),
                section_label="Application Update Requested",
            )
            for update in open_requests
        ]


class ResumeUpdateRequestAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        correct_task = Task.TaskType.PREPARE in self.active_tasks
        in_progress_requests = self.application.current_update_requests().filter(
            status__in=["UPDATE_IN_PROGRESS", "RESPONDED"]
        )

        if correct_status and correct_task and in_progress_requests.exists():
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()
        in_progress_requests = self.application.current_update_requests().filter(
            status__in=["UPDATE_IN_PROGRESS", "RESPONDED"]
        )

        # TODO: There *should* only ever be a single "Resume Update Request" link
        return [
            WorkbasketAction(
                is_post=False,
                name="Resume Update",
                url=reverse(
                    "case:respond-update-request",
                    kwargs=kwargs,
                ),
                section_label="Application Update in Progress",
            )
            for _ in in_progress_requests
        ]


class WithdrawApplicationAction(Action):
    def show_link(self) -> bool:
        show_link = False

        valid_statuses = [
            ImpExpStatus.SUBMITTED,
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
        ]

        if self.status in valid_statuses:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        # "open" instead of WithdrawApplication.STATUS_OPEN to avoid circular dependency
        if self.application.withdrawals.filter(status="open", is_active=True):
            name = "Pending Withdrawal"
        else:
            name = "Request Withdrawal"

        return [
            WorkbasketAction(
                is_post=False,
                name=name,
                url=reverse("case:withdraw-case", kwargs=kwargs),
                section_label="Application Submitted",
            )
        ]


class SubmitVariationUpdateAction(Action):
    def show_link(self) -> bool:
        show_link = False

        if self.status == ImpExpStatus.VARIATION_REQUESTED:
            if Task.TaskType.VR_REQUEST_CHANGE in self.active_tasks:
                show_link = True

        return show_link

    def get_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_kwargs()

        # Didn't use VariationRequest.OPEN to lazily avoid circular dependency
        return kwargs | {
            "variation_request_pk": self.application.variation_requests.get(status="OPEN").pk
        }

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=False,
                name="Submit Update",
                url=reverse("case:variation-request-submit-update", kwargs=kwargs),
                section_label="Update Variation Request",
            )
        ]


# TODO: Revisit when implementing ICMSLST-1400
# Each notification needs a "Acknowledge" "View" and "Clear" action
class AcknowledgeNotificationAction(Action):
    def show_link(self) -> bool:
        show_link = False

        if self.status == ImpExpStatus.COMPLETED and not self.application.is_rejected(
            self.active_tasks
        ):
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        if self.application.acknowledged_by and self.application.acknowledged_datetime:
            action_name = "View Notification"
        else:
            action_name = "Acknowledge Notification"

        # TODO: Revisit when implementing ICMSLST-1400
        # Use this format for each application acknowledgement
        # section_label = f"{action_name}, Notification of {FOO.strftime('%d %b %Y %H:%M:%S')}"

        return [
            WorkbasketAction(
                is_post=False,
                name=action_name,
                url=reverse("case:ack-notification", kwargs=kwargs),
                section_label=action_name,
            )
        ]


# TODO: The show_link logic needs replacing with a "provide report" task.
class ProvideFirearmsReportAction(Action):
    def show_link(self) -> bool:
        if not self.application.is_import_application() or not self.is_importer_user:
            return False

        show_link = False
        correct_status = self.status in [ImpExpStatus.COMPLETED]
        # Can't import ImportApplicationType.Types.FIREARMS
        correct_app_type = self.application.application_type.type == "FA"

        if (
            correct_status
            and correct_app_type
            and not self.application.is_rejected(self.active_tasks)
        ):
            supplementary_info = self._get_supplementary_info()

            if supplementary_info and not supplementary_info.is_complete:
                show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        return [
            WorkbasketAction(
                is_post=False,
                name="Provide Report",
                url=reverse(
                    "import:fa:provide-report", kwargs={"application_pk": self.application.pk}
                ),
                section_label="Firearms Supplementary Reporting",
            )
        ]

    def _get_supplementary_info(self) -> Optional["SupplementaryInfoBase"]:
        supplementary_info = None

        app = self.application
        pt = self.application.process_type

        if pt == ProcessTypes.FA_OIL:
            supplementary_info = app.openindividuallicenceapplication.supplementary_info

        elif pt == ProcessTypes.FA_DFL:
            supplementary_info = app.dflapplication.supplementary_info

        elif pt == ProcessTypes.FA_SIL:
            supplementary_info = app.silapplication.supplementary_info

        return supplementary_info


REQUEST_VARIATION_APPLICANT_ACTIONS: list[ActionT] = [
    EditApplicationAction,
    CancelApplicationAction,
    ViewApplicationAction,
    WithdrawApplicationAction,
    RespondToFurtherInformationRequestAction,
    RespondToUpdateRequestAction,
    ResumeUpdateRequestAction,
    SubmitVariationUpdateAction,
    AcknowledgeNotificationAction,
    ProvideFirearmsReportAction,
]
