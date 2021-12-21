from django.db import models
from django.urls import reverse

from web.domains.user.models import User
from web.domains.workbasket.base import (
    WorkbasketAction,
    WorkbasketBase,
    WorkbasketRow,
    WorkbasketSection,
)
from web.flow.models import Process

from ..models import AccessRequest


class ApprovalRequest(WorkbasketBase, Process):
    """
    Approval request for submitted access requests.
    Approval requests are requested from importer/exporter
    contacts by case officers for access requests by user
    """

    class Meta:
        indexes = [models.Index(fields=["status"], name="AppR_status_idx")]
        ordering = ("-request_date",)

    # Approval Request response options
    APPROVE = "APPROVE"
    REFUSE = "REFUSE"
    RESPONSE_OPTIONS = ((APPROVE, "Approve"), (REFUSE, "Refuse"))

    # Approval Request status
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    STATUSES = (
        (DRAFT, "DRAFT"),
        (OPEN, "OPEN"),
        (CANCELLED, "CANCELLED"),
        (COMPLETED, "COMPLETED"),
    )

    access_request = models.ForeignKey(
        AccessRequest,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="approval_requests",
    )

    status = models.CharField(max_length=20, choices=STATUSES, blank=True, null=True, default=OPEN)
    request_date = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    requested_by = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True, related_name="approval_requests"
    )
    requested_from = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="assigned_approval_requests",
    )
    response = models.CharField(max_length=20, choices=RESPONSE_OPTIONS, blank=True, null=True)
    response_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="responded_approval_requests",
    )
    response_date = models.DateTimeField(blank=True, null=True)
    response_reason = models.CharField(max_length=4000, blank=True, null=True)

    @property
    def is_complete(self):
        return self.status == self.COMPLETED

    def get_workbasket_row(self, user: User) -> WorkbasketRow:
        r = WorkbasketRow()

        r.reference = self.access_request.reference

        r.subject = self.process_type

        acc_req: AccessRequest = self.access_request

        r.company = "\n".join(
            [
                f"{acc_req.submitted_by} {acc_req.submitted_by.email}",
                acc_req.organisation_name,
                acc_req.organisation_address,
            ]
        )

        r.status = self.get_status_display()

        r.timestamp = self.created

        information = "Approval Request"

        actions: list[WorkbasketAction] = []

        if self.process_type == "ExporterApprovalRequest":
            entity = "exporter"
            access_request_pk = acc_req.exporteraccessrequest.pk

        elif self.process_type == "ImporterApprovalRequest":
            entity = "importer"
            access_request_pk = acc_req.importeraccessrequest.pk

        else:
            raise NotImplementedError(f"process_type: {self.process_type} not supported")

        if not self.requested_from:
            actions.append(
                WorkbasketAction(
                    is_post=True,
                    url=reverse(
                        "access:case-approval-take-ownership",
                        kwargs={"pk": self.pk, "entity": entity},
                    ),
                    name="Take Ownership",
                )
            )

        else:
            kwargs = {
                "application_pk": access_request_pk,
                "entity": entity,
                "approval_request_pk": self.pk,
            }

            actions.append(
                WorkbasketAction(
                    is_post=False,
                    url=reverse("access:case-approval-respond", kwargs=kwargs),
                    name="Manage",
                )
            )

        r.sections.append(WorkbasketSection(information=information, actions=actions))

        return r


class ExporterApprovalRequest(ApprovalRequest):
    PROCESS_TYPE = "ExporterApprovalRequest"


class ImporterApprovalRequest(ApprovalRequest):
    PROCESS_TYPE = "ImporterApprovalRequest"
