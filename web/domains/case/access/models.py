from typing import final

import structlog as logging
from django.conf import settings
from django.db import models
from django.utils.functional import cached_property

from web.flow.models import Process, ProcessTypes
from web.types import TypedTextChoices

logger = logging.getLogger(__name__)


class AccessRequest(Process):
    APPROVED = "APPROVED"
    REFUSED = "REFUSED"
    RESPONSES = ((APPROVED, "Approved"), (REFUSED, "Refused"))

    class Meta:
        indexes = [models.Index(fields=["status"], name="AccR_status_idx")]
        ordering = ["submit_datetime"]

    class Statuses(TypedTextChoices):
        SUBMITTED = ("SUBMITTED", "Submitted")
        CLOSED = ("CLOSED", "Closed")
        FIR_REQUESTED = ("FIR_REQUESTED", "Processing (FIR)")

    reference = models.CharField(max_length=100, blank=False, null=False, unique=True)

    status = models.CharField(
        max_length=30, choices=Statuses.choices, blank=False, null=False, default=Statuses.SUBMITTED
    )

    organisation_name = models.CharField(max_length=100, blank=False, null=False)
    organisation_address = models.TextField()
    organisation_registered_number = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="Registered Number",
        help_text="Companies House Company Number",
    )
    request_reason = models.TextField(
        verbose_name="What are you importing and where are you importing it from?"
    )
    agent_name = models.CharField(max_length=100, blank=True, null=True)
    agent_address = models.TextField(blank=True, default="")

    submit_datetime = models.DateTimeField(auto_now=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="submitted_access_requests",
    )
    last_update_datetime = models.DateTimeField(auto_now=True, blank=False, null=False)
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="updated_access_requests",
    )
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="closed_access_requests",
    )
    response = models.CharField(max_length=20, choices=RESPONSES, blank=False, null=True)
    response_reason = models.TextField(blank=True, default="")

    further_information_requests = models.ManyToManyField("web.FurtherInformationRequest")

    @cached_property
    def submitted_by_email(self):
        if self.submitted_by:
            return self.submitted_by.email
        return None


@final
class ImporterAccessRequest(AccessRequest):
    PROCESS_TYPE = ProcessTypes.IAR
    IS_FINAL = True

    AGENT_ACCESS = "AGENT_IMPORTER_ACCESS"
    REQUEST_TYPES = (
        ("MAIN_IMPORTER_ACCESS", "Request access to act as an Importer"),
        (AGENT_ACCESS, "Request access to act as an Agent for an Importer"),
    )
    eori_number = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="EORI Number",
        help_text="EORI number should include the GB prefix for organisation or GBPR for individual",
    )

    link = models.ForeignKey(
        "web.Importer",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="access_requests",
    )
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPES, verbose_name="Access Request Type"
    )


@final
class ExporterAccessRequest(AccessRequest):
    PROCESS_TYPE = ProcessTypes.EAR
    IS_FINAL = True

    AGENT_ACCESS = "AGENT_EXPORTER_ACCESS"
    REQUEST_TYPES = (
        ("MAIN_EXPORTER_ACCESS", "Request access to act as an Exporter"),
        (AGENT_ACCESS, "Request access to act as an Agent for an Exporter"),
    )

    link = models.ForeignKey(
        "web.Exporter",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="access_requests",
    )
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPES, verbose_name="Access Request Type"
    )
