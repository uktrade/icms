from typing import Any

from django.conf import settings
from django.urls import reverse

from web.domains.case.shared import ImpExpStatus
from web.domains.workbasket.base import WorkbasketAction
from web.models import Task

from .base import Action, ActionT

"""Actions that only apply to ilb admin users are added here"""


class TakeOwnershipAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [ImpExpStatus.SUBMITTED, ImpExpStatus.VARIATION_REQUESTED]
        no_case_owner = not self.application.case_owner

        if correct_status and no_case_owner:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        section_label = "Application Processing"
        if Task.TaskType.PREPARE in self.active_tasks:
            section_label += "\nOut for Update"

        return [
            WorkbasketAction(
                is_post=True,
                name="Take Ownership",
                url=reverse("case:take-ownership", kwargs=kwargs),
                section_label=section_label,
            )
        ]


class ViewApplicationCaseAction(Action):
    """Case officer "View Case" link"""

    # Used for sorting the view link in to a section (this is the default)
    section_label = "Application Processing"

    def show_link(self) -> bool:
        show_link = False

        # A freshly submitted application (no case_owner yet)
        if self.status == ImpExpStatus.SUBMITTED and not self.application.case_owner:
            show_link = True
            if Task.TaskType.PREPARE in self.active_tasks:
                self.section_label += "\nOut for Update"

        elif self.status == ImpExpStatus.PROCESSING:
            # An application being processed by another ilb admin
            if not self.is_case_owner():
                show_link = True

            # An authorised application
            elif Task.TaskType.AUTHORISE in self.active_tasks:
                show_link = True
                self.section_label = "Authorise Documents"

            # App in CHIEF wait state
            elif Task.TaskType.CHIEF_WAIT in self.active_tasks:
                show_link = True

            # App in CHIEF error state
            elif Task.TaskType.CHIEF_ERROR in self.active_tasks:
                show_link = True

            elif (
                Task.TaskType.DOCUMENT_SIGNING in self.active_tasks
                or Task.TaskType.DOCUMENT_ERROR in self.active_tasks
            ):
                show_link = True
                self.section_label = "Authorise Documents"

        # An application being processed by another ilb admin (via a variation request)
        elif self.status == ImpExpStatus.VARIATION_REQUESTED and not self.is_case_owner():
            show_link = True

        # An application rejected by the current case officer
        elif (
            self.status == ImpExpStatus.COMPLETED
            and Task.TaskType.REJECTED in self.active_tasks
            and self.is_case_owner()
        ):
            show_link = True
            self.section_label = "View Case"

        # App being revoked
        elif self.status == ImpExpStatus.REVOKED:
            if Task.TaskType.CHIEF_REVOKE_WAIT in self.active_tasks:
                show_link = True
                self.section_label = "CHIEF Wait for Revocation"

            elif Task.TaskType.CHIEF_ERROR in self.active_tasks:
                show_link = True
                self.section_label = "CHIEF Error"

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        if (
            (self.status == ImpExpStatus.COMPLETED and Task.TaskType.REJECTED in self.active_tasks)
            or Task.TaskType.AUTHORISE in self.active_tasks
            or Task.TaskType.DOCUMENT_SIGNING in self.active_tasks
            or Task.TaskType.DOCUMENT_ERROR in self.active_tasks
            or Task.TaskType.CHIEF_WAIT in self.active_tasks
            or Task.TaskType.CHIEF_REVOKE_WAIT in self.active_tasks
        ):
            name = "View Case"
        else:
            name = "View"

        return [
            WorkbasketAction(
                is_post=False,
                name=name,
                url=reverse("case:manage", kwargs=kwargs),
                section_label=self.section_label,
            )
        ]


class ManageWithdrawApplicationAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [
            ImpExpStatus.SUBMITTED,
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
        ]

        correct_task = Task.TaskType.PROCESS in self.active_tasks

        if correct_status and correct_task and self.application.annotation_has_withdrawal:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        if self.is_case_owner():
            name = "Withdrawal Request"
        else:
            name = "View Withdrawal Request"

        return [
            WorkbasketAction(
                is_post=False,
                name=name,
                url=reverse("case:manage-withdrawals", kwargs=kwargs),
                section_label="Withdraw Pending",
            )
        ]


class ManageApplicationAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        correct_task = self.has_task(Task.TaskType.PROCESS, Task.TaskType.PREPARE)

        if self.is_case_owner() and correct_status and correct_task:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        section_label = "Application Processing"

        if Task.TaskType.PREPARE in self.active_tasks:
            section_label += ", Out for Update"

        if self.application.annotation_open_fir_pks:
            section_label += ", Further Information Requested"

        return [
            WorkbasketAction(
                is_post=False,
                name="Manage",
                url=reverse("case:manage", kwargs=kwargs),
                section_label=section_label,
            )
        ]


class AuthoriseDocumentsAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        correct_task = Task.TaskType.AUTHORISE in self.active_tasks

        if self.is_case_owner() and correct_status and correct_task:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=False,
                name="Authorise Documents",
                url=reverse("case:authorise-documents", kwargs=kwargs),
                section_label="Authorise Documents",
            )
        ]


class CancelAuthorisationAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        correct_task = Task.TaskType.AUTHORISE in self.active_tasks

        if self.is_case_owner() and correct_status and correct_task:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=True,
                name="Cancel Authorisation",
                url=reverse("case:cancel-authorisation", kwargs=kwargs),
                section_label="Authorise Documents",
            )
        ]


class CheckCaseDocumentGenerationAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        correct_task = Task.TaskType.DOCUMENT_SIGNING in self.active_tasks

        if self.is_case_owner() and correct_status and correct_task:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=False,
                name="Monitor Progress",
                url=reverse("case:check-document-generation", kwargs=kwargs),
                section_label="Digital Signing",
                is_ajax=True,
            )
        ]


class RecreateCaseDocumentsAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED]
        correct_task = Task.TaskType.DOCUMENT_ERROR in self.active_tasks

        if self.is_case_owner() and correct_status and correct_task:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=True,
                name="Recreate Case Documents",
                url=reverse("case:recreate-case-documents", kwargs=kwargs),
                section_label="Digital Signing Failed",
            )
        ]


class BypassChiefSuccessAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
        ]
        correct_task = Task.TaskType.CHIEF_WAIT in self.active_tasks
        correct_setting = (
            not settings.SEND_LICENCE_TO_CHIEF and settings.ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD
        )

        if correct_status and correct_task and correct_setting:
            show_link = True

        if (
            self.status == ImpExpStatus.REVOKED
            and Task.TaskType.CHIEF_REVOKE_WAIT in self.active_tasks
            and correct_setting
        ):
            show_link = True

        return show_link

    def get_kwargs(self) -> dict[str, Any]:
        return {"application_pk": self.application.pk, "chief_status": "success"}

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        if self.status == ImpExpStatus.REVOKED:
            section_label = "CHIEF Wait for Revocation"
        else:
            section_label = "CHIEF Wait"

        return [
            WorkbasketAction(
                is_post=True,
                name="(TEST) Bypass CHIEF",
                url=reverse("import:bypass-chief", kwargs=kwargs),
                section_label=section_label,
            )
        ]


class BypassChiefFailureAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
        ]
        correct_task = Task.TaskType.CHIEF_WAIT in self.active_tasks
        correct_setting = (
            not settings.SEND_LICENCE_TO_CHIEF and settings.ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD
        )

        if correct_status and correct_task and correct_setting:
            show_link = True

        return show_link

    def get_kwargs(self) -> dict[str, Any]:
        return {"application_pk": self.application.pk, "chief_status": "failure"}

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        return [
            WorkbasketAction(
                is_post=True,
                name="(TEST) Bypass CHIEF induce failure",
                url=reverse("import:bypass-chief", kwargs=kwargs),
                section_label="CHIEF Wait",
            )
        ]


class ChiefMonitorProgressAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
        ]
        correct_task = Task.TaskType.CHIEF_WAIT in self.active_tasks

        if correct_status and correct_task:
            show_link = True

        if (
            self.status == ImpExpStatus.REVOKED
            and Task.TaskType.CHIEF_REVOKE_WAIT in self.active_tasks
        ):
            show_link = True

        return show_link

    def get_kwargs(self) -> dict[str, Any]:
        return {"application_pk": self.application.pk}

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        kwargs = self.get_kwargs()

        if self.status == ImpExpStatus.REVOKED:
            section_label = "CHIEF Wait for Revocation"
        else:
            section_label = "CHIEF Wait"

        return [
            WorkbasketAction(
                is_post=False,
                name="Monitor Progress",
                url=reverse("chief:check-progress", kwargs=kwargs),
                is_ajax=True,
                section_label=section_label,
            )
        ]


class ChiefShowLicenceDetailsAction(Action):
    def show_link(self) -> bool:
        show_link = False

        correct_status = self.status in [
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
            ImpExpStatus.REVOKED,
        ]
        correct_task = Task.TaskType.CHIEF_ERROR in self.active_tasks

        if correct_status and correct_task:
            show_link = True

        return show_link

    def get_workbasket_actions(self) -> list[WorkbasketAction]:
        return [
            WorkbasketAction(
                is_post=False,
                name="Show Licence Details",
                url=reverse("chief:failed-licences"),
                section_label="CHIEF Error",
            )
        ]


CASEWORKER_ACTIONS: list[ActionT] = [
    #
    # Management actions
    TakeOwnershipAction,
    ManageApplicationAction,
    ManageWithdrawApplicationAction,
    AuthoriseDocumentsAction,
    CancelAuthorisationAction,
    #
    # Document Signing actions
    CheckCaseDocumentGenerationAction,
    RecreateCaseDocumentsAction,
    #
    # Chief actions
    BypassChiefSuccessAction,
    BypassChiefFailureAction,
    ChiefMonitorProgressAction,
    ChiefShowLicenceDetailsAction,
    #
    # View application action
    ViewApplicationCaseAction,
]
