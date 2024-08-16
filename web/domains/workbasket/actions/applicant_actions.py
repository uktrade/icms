import datetime as dt
from typing import Any

from django.urls import reverse
from django.utils.dateparse import parse_datetime

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import DocumentPack
from web.domains.workbasket.base import WorkbasketAction
from web.models import Task
from web.permissions import Perms
from web.utils import datetime_format

from .base import Action, ActionT

"""Actions that only apply to importer/exporter users are added here"""


class EditApplicationAction(Action):
    """Applicant action to resume editing the application"""

    def show_link(self) -> bool:
        show_link = False

        if self.status == ImpExpStatus.IN_PROGRESS and self.app_checker.can_edit():
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

        if self.status == ImpExpStatus.IN_PROGRESS and self.app_checker.can_edit():
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

        if self.status in valid_statuses and self.app_checker.can_view():
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


class ClearApplicationAction(Action):
    def show_link(self) -> bool:
        show_link = False

        if self.status in [ImpExpStatus.COMPLETED, ImpExpStatus.REVOKED]:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=True,
                name="Clear",
                url=reverse("case:clear", kwargs=kwargs),
                section_label="Application View",
            )
        ]


class RespondToFurtherInformationRequestAction(Action):
    def show_link(self) -> bool:
        correct_status = self.status in [
            ImpExpStatus.SUBMITTED,
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
        ]

        return (
            correct_status
            and self.application.annotation_open_fir_pairs
            and self.app_checker.can_edit()
        )

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=False,
                name="Respond",
                url=reverse("case:respond-fir", kwargs=kwargs | {"fir_pk": fir_pk}),
                section_label=f"Further Information Request, {self.fmt_fir_dt(requested_datetime)}",
            )
            for fir_pk, requested_datetime in self.application.annotation_open_fir_pairs
        ]

    @staticmethod
    def fmt_fir_dt(requested_datetime: dt.datetime) -> str:
        return datetime_format(parse_datetime(requested_datetime), "%d %b %Y %H:%M:%S")


class RespondToUpdateRequestAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [
            ImpExpStatus.SUBMITTED,
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
        ]
        correct_task = Task.TaskType.PREPARE in self.active_tasks
        can_edit = self.app_checker.can_edit()

        if correct_status and correct_task and self.application.annotation_open_ur_pks and can_edit:
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

        correct_status = self.status in [
            ImpExpStatus.SUBMITTED,
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
        ]
        correct_task = Task.TaskType.PREPARE in self.active_tasks
        can_edit = self.app_checker.can_edit()

        if (
            correct_status
            and correct_task
            and self.application.annotation_has_in_progress_ur
            and can_edit
        ):
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

        can_edit = self.app_checker.can_edit()
        if self.status in valid_statuses and can_edit:
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

        correct_status = self.status == ImpExpStatus.VARIATION_REQUESTED
        correct_task = Task.TaskType.VR_REQUEST_CHANGE in self.active_tasks
        can_edit = self.app_checker.can_edit()

        if correct_status and correct_task and can_edit:
            show_link = True

        return show_link

    def get_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_kwargs()

        # Didn't use VariationRequest.Statuses.OPEN to lazily avoid circular dependency
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

    def show_link(self) -> bool:
        show_link = False

        if (
            self.status == ImpExpStatus.COMPLETED
            and Task.TaskType.REJECTED not in self.active_tasks
            and self.app_checker.can_edit()
            and self.issued_documents()
        ):
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        raise NotImplementedError

    @staticmethod
    def section_label(pack: DocumentPack) -> str:
        issue_datetime = datetime_format(pack.case_completion_datetime, "%d-%b-%Y %H:%M")

        return f"Documents Issued {issue_datetime}"

    def issued_documents(self) -> list:
        """Cache the issued documents on the application to prevent duplicate queries."""
        if not hasattr(self.application, "_wb_cache_issued_documents_list"):
            issued_document_qs = document_pack.pack_workbasket_get_issued(
                self.application.get_specific_model(), self.user
            )

            self.application._wb_cache_issued_documents_list = list(
                issued_document_qs.values_list("pk", "case_completion_datetime", named=True)
            )

        return self.application._wb_cache_issued_documents_list


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
            for i in self.issued_documents()
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
            for i in self.issued_documents()
        ]


class ProvideFirearmsReportAction(Action):
    def show_link(self) -> bool:
        if not self.application.is_import_application() or not self.user.has_perm(
            Perms.sys.importer_access
        ):
            return False

        show_link = False
        correct_status = self.status in [ImpExpStatus.COMPLETED]
        not_rejected = Task.TaskType.REJECTED not in self.active_tasks
        # Can't import ImportApplicationType.Types.FIREARMS
        correct_app_type = self.application.application_type.type == "FA"
        can_edit = self.app_checker.can_edit()

        if correct_status and correct_app_type and not_rejected and can_edit:
            supplementary_info = self.application.get_specific_model().supplementary_info

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


APPLICANT_ACTIONS: list[ActionT] = [
    EditApplicationAction,
    CancelApplicationAction,
    ViewApplicationAction,
    ClearApplicationAction,
    WithdrawApplicationAction,
    RespondToFurtherInformationRequestAction,
    RespondToUpdateRequestAction,
    ResumeUpdateRequestAction,
    SubmitVariationUpdateAction,
    ViewIssuedDocumentsAction,
    ClearIssuedDocumentsAction,
    ProvideFirearmsReportAction,
]
