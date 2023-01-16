from django.db import models

from web.domains.user.models import User
from web.flow.models import Process, ProcessTypes

from ..models import AccessRequest


class ApprovalRequest(Process):
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
    response_reason = models.TextField(blank=True, null=True)

    @property
    def is_complete(self):
        return self.status == self.COMPLETED


class ExporterApprovalRequest(ApprovalRequest):
    PROCESS_TYPE = ProcessTypes.ExpApprovalReq


class ImporterApprovalRequest(ApprovalRequest):
    PROCESS_TYPE = ProcessTypes.ImpApprovalReq
