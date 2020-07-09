from django.db import models

from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import CaseNote, UpdateRequest, VariationRequest
from web.domains.user.models import User


class ExportCase(models.Model):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    WITHDRAWN = "WITHDRAWN"
    STOPPED = "STOPPED"
    VARIATION_REQUESTED = "VARIATION"
    REVOKED = "REVOKED"
    DELETED = "DELETED"

    STATUSES = (
        (IN_PROGRESS, "In Progress"),
        (SUBMITTED, "Submitted"),
        (PROCESSING, "Processing"),
        (COMPLETED, "Completed"),
        (WITHDRAWN, "Withdrawn"),
        (STOPPED, "Stopped"),
        (REVOKED, "Revoked"),
        (VARIATION_REQUESTED, "Case Variation"),
        (DELETED, "Deleted"),
    )

    # Decision
    REFUSE = "REFUSE"
    APPROVE = "APPROVE"
    DECISIONS = ((REFUSE, "Refuse"), (APPROVE, "Approve"))

    status = models.CharField(max_length=30, choices=STATUSES, blank=False, null=False)
    reference = models.CharField(max_length=50, blank=True, null=True)
    variation_no = models.IntegerField(blank=False, null=False, default=0)
    decision = models.CharField(max_length=10, choices=DECISIONS, blank=True, null=True)
    refuse_reason = models.CharField(max_length=4000, blank=True, null=True)
    last_update_datetime = models.DateTimeField(blank=False, null=False, auto_now=True)
    last_updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=False, null=False, related_name="updated_export_cases"
    )
    variation_requests = models.ManyToManyField(VariationRequest)
    case_notes = models.ManyToManyField(CaseNote)
    further_information_requests = models.ManyToManyField(FurtherInformationRequest)
    update_requests = models.ManyToManyField(UpdateRequest)
    case_notes = models.ManyToManyField(CaseNote)
