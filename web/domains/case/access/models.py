import structlog as logging
from django.db import models
from django.urls import reverse

from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.domains.workbasket.base import WorkbasketBase
from web.domains.user.models import User
from web.flow.models import Process


logger = logging.getLogger(__name__)


class AccessRequest(WorkbasketBase, Process):
    APPROVED = "APPROVED"
    REFUSED = "REFUSED"
    RESPONSES = ((APPROVED, "Approved"), (REFUSED, "Refused"))

    SUBMITTED = "SUBMITTED"
    CLOSED = "CLOSED"
    STATUSES = ((SUBMITTED, "Submitted"), (CLOSED, "Closed"))

    reference = models.CharField(max_length=50, blank=False, null=False)
    status = models.CharField(
        max_length=30, choices=STATUSES, blank=False, null=False, default=SUBMITTED
    )
    organisation_name = models.CharField(max_length=100, blank=False, null=False)
    organisation_address = models.TextField()
    organisation_registered_number = models.CharField(
        max_length=100, blank=True, default="", verbose_name="Registered Number"
    )
    request_reason = models.TextField(
        verbose_name="What are you importing and where are you importing it from?"
    )
    agent_name = models.CharField(max_length=100, blank=True, null=True)
    agent_address = models.TextField(blank=True, default="")

    submit_datetime = models.DateTimeField(auto_now=True)
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="submitted_access_requests",
    )
    last_update_datetime = models.DateTimeField(auto_now=True, blank=False, null=False)
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="updated_access_requests",
    )
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="closed_access_requests"
    )
    response = models.CharField(max_length=20, choices=RESPONSES, blank=False, null=True)
    response_reason = models.TextField(blank=True, default="")

    further_information_requests = models.ManyToManyField(FurtherInformationRequest)

    def get_workbasket_template(self):
        return "web/domains/workbasket/partials/access-request.html"

    def get_task_url(self, task, user):
        if task.task_type == "notify":
            return reverse("access:management", kwargs={"pk": self.pk})
        else:
            raise Exception(f"Unknown task_type {task.task_type}")


class ImporterAccessRequest(AccessRequest):
    PROCESS_TYPE = "ImporterAccessRequest"

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
    eori_number_ni = models.CharField(
        max_length=20, blank=True, default="", verbose_name="NI EORI Number"
    )

    link = models.ForeignKey(
        Importer, on_delete=models.PROTECT, blank=True, null=True, related_name="access_requests"
    )
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPES, verbose_name="Access Request Type",
    )


class ExporterAccessRequest(AccessRequest):
    PROCESS_TYPE = "ExporterAccessRequest"

    AGENT_ACCESS = "AGENT_EXPORTER_ACCESS"
    REQUEST_TYPES = (
        ("MAIN_EXPORTER_ACCESS", "Request access to act as an Exporter"),
        (AGENT_ACCESS, "Request access to act as an Agent for an Exporter"),
    )

    link = models.ForeignKey(
        Exporter, on_delete=models.PROTECT, blank=True, null=True, related_name="access_requests"
    )
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPES, verbose_name="Access Request Type",
    )
