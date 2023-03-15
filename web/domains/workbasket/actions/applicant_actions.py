from typing import TYPE_CHECKING, Any, Optional

from django.urls import reverse
from django.utils.dateparse import parse_datetime

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.workbasket.base import WorkbasketAction
from web.flow.models import ProcessTypes
from web.models import Task

from .base import Action, ActionT

if TYPE_CHECKING:
    from web.domains.case._import.fa.models import SupplementaryInfoBase
    from web.domains.case.types import DocumentPack

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
            ImpExpStatus.REVOKED,
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
            ImpExpStatus.REVOKED: "Application View",
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

        return correct_status and self.application.annotation_open_fir_pairs

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=False,
                name="Respond",
                url=reverse("case:respond-fir", kwargs=kwargs | {"fir_pk": fir_pk}),
                section_label=f"Further Information Request, {parse_datetime(requested_datetime).strftime('%d %b %Y %H:%M:%S')}",
            )
            for fir_pk, requested_datetime in self.application.annotation_open_fir_pairs
        ]


class RespondToUpdateRequestAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        correct_task = Task.TaskType.PREPARE in self.active_tasks

        if correct_status and correct_task and self.application.annotation_open_ur_pks:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        # Note: There *should* only ever be a single "Respond to Update Request" link
        return [
            WorkbasketAction(
                is_post=False,
                name="Respond to Update Request",
                url=reverse(
                    "case:start-update-request",
                    kwargs=kwargs | {"update_request_pk": update_pk},
                ),
                section_label="Application Update Requested",
            )
            for update_pk in self.application.annotation_open_ur_pks
        ]


class ResumeUpdateRequestAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        correct_task = Task.TaskType.PREPARE in self.active_tasks

        if correct_status and correct_task and self.application.annotation_has_in_progress_ur:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

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

        if self.application.annotation_has_withdrawal:
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


class IssuedDocumentsBaseAction(Action):
    """Base class for viewing issued documents and clearing those documents from the workbasket"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.issued_documents_qs = document_pack.pack_workbasket_get_issued(
            self.application.get_specific_model()
        )

    def show_link(self) -> bool:
        show_link = False

        if (
            self.status == ImpExpStatus.COMPLETED
            and not self.is_rejected
            and self.issued_documents_qs.exists()
        ):
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        raise NotImplementedError

    @staticmethod
    def section_label(pack: "DocumentPack") -> str:
        cd = pack.case_completion_datetime
        issue_datetime = cd.strftime("%d-%b-%Y %H:%M")

        return f"Documents Issued {issue_datetime}"


class ViewIssuedDocumentsAction(IssuedDocumentsBaseAction):
    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=False,
                name="View Issued Documents",
                url=reverse(
                    "case:view-issued-case-documents", kwargs=kwargs | {"issued_document_pk": i.pk}
                ),
                section_label=self.section_label(i),
            )
            for i in self.issued_documents_qs.values_list(
                "pk", "case_completion_datetime", named=True
            )
        ]


class ClearIssuedDocumentsAction(IssuedDocumentsBaseAction):
    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=True,
                name="Clear",
                url=reverse(
                    "case:clear-issued-case-documents", kwargs=kwargs | {"issued_document_pk": i.pk}
                ),
                section_label=self.section_label(i),
            )
            for i in self.issued_documents_qs.values_list(
                "pk", "case_completion_datetime", named=True
            )
        ]


class ProvideFirearmsReportAction(Action):
    def show_link(self) -> bool:
        if not self.application.is_import_application() or not self.is_importer_user:
            return False

        show_link = False
        correct_status = self.status in [ImpExpStatus.COMPLETED]
        # Can't import ImportApplicationType.Types.FIREARMS
        correct_app_type = self.application.application_type.type == "FA"

        if correct_status and correct_app_type and not self.is_rejected:
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
    ViewIssuedDocumentsAction,
    ClearIssuedDocumentsAction,
    ProvideFirearmsReportAction,
]
