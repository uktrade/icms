from django.db import models

from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import CaseNote, UpdateRequest, VariationRequest
from web.domains.country.models import Country, CountryGroup
from web.domains.exporter.models import Exporter
from web.domains.office.models import Office
from web.domains.user.models import User


class ExportApplicationType(models.Model):

    is_active = models.BooleanField(blank=False, null=False, default=True)
    type_code = models.CharField(max_length=30, blank=False, null=False)
    type = models.CharField(max_length=70, blank=False, null=False)
    allow_multiple_products = models.BooleanField(blank=False, null=False)
    generate_cover_letter = models.BooleanField(blank=False, null=False)
    allow_hse_authorization = models.BooleanField(blank=False, null=False)
    country_group = models.ForeignKey(
        CountryGroup, on_delete=models.PROTECT, blank=False, null=False
    )
    country_group_for_manufacture = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="manufacture_export_application_types",
    )


class ExportApplication(models.Model):
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

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(max_length=30, choices=STATUSES, blank=False, null=False)
    reference = models.CharField(max_length=50, blank=True, null=True)
    application_type = models.ForeignKey(
        ExportApplicationType, on_delete=models.PROTECT, blank=False, null=False
    )
    decision = models.CharField(max_length=10, choices=DECISIONS, blank=True, null=True)
    refuse_reason = models.CharField(max_length=4000, blank=True, null=True)
    last_update_datetime = models.DateTimeField(blank=False, null=False, auto_now=True)
    last_updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=False, null=False, related_name="updated_export_cases"
    )
    variation_requests = models.ManyToManyField(VariationRequest)
    variation_no = models.IntegerField(blank=False, null=False, default=0)
    case_notes = models.ManyToManyField(CaseNote)
    further_information_requests = models.ManyToManyField(FurtherInformationRequest)
    update_requests = models.ManyToManyField(UpdateRequest)
    submit_datetime = models.DateTimeField(blank=True, null=True)
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="submitted_export_application",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="created_export_applications",
    )
    exporter = models.ForeignKey(
        Exporter,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="export_applications",
    )
    exporter_office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        blank=False,
        null=True,
        related_name="office_export_applications",
    )
    contact = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="contact_export_applications",
    )
    countries = models.ManyToManyField(Country)
    agent = models.ForeignKey(
        Exporter,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="agent_export_applications",
    )
    agent_office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="agent_office_export_applications",
    )
