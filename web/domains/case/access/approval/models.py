from django.conf import settings
from django.db import models

from web.flow.models import Process, ProcessTypes
from web.types import TypedTextChoices


class ApprovalRequest(Process):
    """
    Approval request for submitted access requests.
    Approval requests are requested from importer/exporter
    contacts by case officers for access requests by user
    """

    class Meta:
        indexes = [models.Index(fields=["status"], name="AppR_status_idx")]
        ordering = ("-request_date",)

    class Responses(TypedTextChoices):
        APPROVE = ("APPROVE", "Approve")
        REFUSE = ("REFUSE", "Refuse")

    class Statuses(TypedTextChoices):
        DRAFT = ("DRAFT", "DRAFT")
        OPEN = ("OPEN", "OPEN")
        CANCELLED = ("CANCELLED", "CANCELLED")
        COMPLETED = ("COMPLETED", "COMPLETED")

    access_request = models.ForeignKey(
        "web.AccessRequest",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="approval_requests",
    )

    status = models.CharField(
        max_length=20, choices=Statuses.choices, blank=True, null=True, default=Statuses.OPEN
    )
    request_date = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="approval_requests",
    )
    requested_from = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="assigned_approval_requests",
    )
    response = models.CharField(max_length=20, choices=Responses.choices, blank=True, null=True)
    response_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="responded_approval_requests",
    )
    response_date = models.DateTimeField(blank=True, null=True)
    response_reason = models.TextField(blank=True, null=True)

    @property
    def is_complete(self):
        return self.status == self.Statuses.COMPLETED


class ExporterApprovalRequest(ApprovalRequest):
    PROCESS_TYPE = ProcessTypes.ExpApprovalReq


class ImporterApprovalRequest(ApprovalRequest):
    PROCESS_TYPE = ProcessTypes.ImpApprovalReq
