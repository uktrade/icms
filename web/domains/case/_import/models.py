from django.db import models
from django.utils import timezone

from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import CaseNote, UpdateRequest, VariationRequest
from web.domains.commodity.models import CommodityGroup, CommodityType
from web.domains.country.models import Country, CountryGroup
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.template.models import Template
from web.domains.user.models import User
from web.domains.workbasket.base import WorkbasketBase
from web.flow.models import Process


class ImportApplicationType(models.Model):
    TYPE_FIREARMS_AMMUNITION_CODE = "FA"
    TYPE_SANCTION_ADHOC = "SAN_ADHOC_TEMP"  # TODO: missing from legacy data extract, hence TEMP
    TYPE_WOOD_QUOTA = "WD"
    TYPE_DEGROGATION_FROM_SANCTIONS_BAN = "SAN"

    TYPE = (
        (TYPE_FIREARMS_AMMUNITION_CODE, "Firearms and Ammunition"),
        (TYPE_DEGROGATION_FROM_SANCTIONS_BAN, "Derogation from Sanctions Import Ban"),
        (TYPE_SANCTION_ADHOC, "Sanctions and Adhoc"),
        (TYPE_WOOD_QUOTA, "Wood (Quota)"),
    )

    SUBTYPE_OPEN_INDIVIDUAL_LICENCE = "OIL"
    SUBTYPE = ((SUBTYPE_OPEN_INDIVIDUAL_LICENCE, "Open Individual Import Licence"),)

    is_active = models.BooleanField(blank=False, null=False)
    type = models.CharField(max_length=70, blank=False, null=False, choices=TYPE)
    sub_type = models.CharField(max_length=70, blank=True, null=True, choices=SUBTYPE)
    licence_type_code = models.CharField(max_length=20, blank=False, null=False)
    sigl_flag = models.BooleanField(blank=False, null=False)
    chief_flag = models.BooleanField(blank=False, null=False)
    chief_licence_prefix = models.CharField(max_length=10, blank=True, null=True)
    paper_licence_flag = models.BooleanField(blank=False, null=False)
    electronic_licence_flag = models.BooleanField(blank=False, null=False)
    cover_letter_flag = models.BooleanField(blank=False, null=False)
    cover_letter_schedule_flag = models.BooleanField(blank=False, null=False)
    category_flag = models.BooleanField(blank=False, null=False)
    sigl_category_prefix = models.CharField(max_length=100, blank=True, null=True)
    chief_category_prefix = models.CharField(max_length=10, blank=True, null=True)
    default_licence_length_months = models.IntegerField(blank=True, null=True)
    endorsements_flag = models.BooleanField(blank=False, null=False)
    default_commodity_desc = models.CharField(max_length=200, blank=True, null=True)
    quantity_unlimited_flag = models.BooleanField(blank=False, null=False)
    unit_list_csv = models.CharField(max_length=200, blank=True, null=True)
    exp_cert_upload_flag = models.BooleanField(blank=False, null=False)
    supporting_docs_upload_flag = models.BooleanField(blank=False, null=False)
    multiple_commodities_flag = models.BooleanField(blank=False, null=False)
    guidance_file_url = models.CharField(max_length=4000, blank=True, null=True)
    licence_category_description = models.CharField(max_length=1000, blank=True, null=True)

    usage_auto_category_desc_flag = models.BooleanField(blank=False, null=False)
    case_checklist_flag = models.BooleanField(blank=False, null=False)
    importer_printable = models.BooleanField(blank=False, null=False)
    origin_country_group = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="import_application_types_from",
    )
    consignment_country_group = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="import_application_types_to",
    )
    master_country_group = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="import_application_types",
    )
    commodity_type = models.ForeignKey(
        CommodityType, on_delete=models.PROTECT, blank=True, null=True
    )
    declaration_template = models.ForeignKey(
        Template,
        on_delete=models.PROTECT,
        blank=False,
        null=True,  # TODO: decide if we're going to use this or not; made nullable for now so we can have this table populated
        related_name="declaration_application_types",
    )
    endorsements = models.ManyToManyField(Template, related_name="endorsement_application_types")
    default_commodity_group = models.ForeignKey(
        CommodityGroup, on_delete=models.PROTECT, blank=True, null=True
    )

    def get_type_description(self):
        type_name = self.get_type_display()
        sub_type_name = self.get_sub_type_display()
        if sub_type_name:
            title = f"{type_name} {sub_type_name}"
        else:
            title = type_name
        return title

    def __str__(self):
        if self.sub_type:
            return f"{self.type} ({self.sub_type})"
        else:
            return f"{self.type}"

    class Meta:
        ordering = ("type", "sub_type")


class ImportApplication(WorkbasketBase, Process):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    WITHDRAWN = "WITHDRAWN"
    STOPPED = "STOPPED"
    VARIATION_REQUESTED = "VARIATION_REQUESTED"
    REVOKED = "REVOKED"
    DELETED = "DELETED"
    UPDATE_REQUESTED = "UPDATE_REQUESTED"

    STATUSES = (
        (IN_PROGRESS, "In Progress"),
        (SUBMITTED, "Submitted"),
        (PROCESSING, "Processing"),
        (COMPLETED, "Completed"),
        (WITHDRAWN, "Withdrawn"),
        (STOPPED, "Stopped"),
        (REVOKED, "Revoked"),
        (VARIATION_REQUESTED, "Variation Requested"),
        (DELETED, "Deleted"),
        (UPDATE_REQUESTED, "Update Requested"),
    )

    # Chief usage status
    CANCELLED = "C"
    EXHAUSTED = "E"
    EXPIRED = "D"
    SURRENDERED = "S"
    CHIEF_STATUSES = (
        (CANCELLED, "Cancelled"),
        (EXHAUSTED, "Exhausted"),
        (EXPIRED, "Expired"),
        (SURRENDERED, "S"),
    )

    # Decision
    REFUSE = "REFUSE"
    APPROVE = "APPROVE"
    DECISIONS = ((APPROVE, "Approve"), (REFUSE, "Refuse"))

    status = models.CharField(
        max_length=30, choices=STATUSES, blank=False, null=False, default=IN_PROGRESS
    )
    reference = models.CharField(max_length=100, blank=True, null=True)
    applicant_reference = models.CharField(max_length=500, blank=True, null=True)
    submit_datetime = models.DateTimeField(blank=True, null=True)
    create_datetime = models.DateTimeField(blank=False, null=False, auto_now_add=True)
    variation_no = models.IntegerField(blank=False, null=False, default=0)
    legacy_case_flag = models.BooleanField(blank=False, null=False, default=False)
    chief_usage_status = models.CharField(
        max_length=1, choices=CHIEF_STATUSES, blank=True, null=True
    )
    under_appeal_flag = models.BooleanField(blank=False, null=False, default=False)
    decision = models.CharField(max_length=10, choices=DECISIONS, blank=True, null=True)
    variation_decision = models.CharField(max_length=10, choices=DECISIONS, blank=True, null=True)
    refuse_reason = models.CharField(max_length=4000, blank=True, null=True)
    variation_refuse_reason = models.CharField(max_length=4000, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    licence_start_date = models.DateField(blank=True, null=True)
    licence_end_date = models.DateField(blank=True, null=True)
    licence_extended_flag = models.BooleanField(blank=False, null=False, default=False)
    last_update_datetime = models.DateTimeField(blank=False, null=False, auto_now=True)
    application_type = models.ForeignKey(
        ImportApplicationType, on_delete=models.PROTECT, blank=False, null=False
    )
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="submitted_import_applications",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="created_import_applications",
    )
    last_updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=False, null=False, related_name="updated_import_cases"
    )
    importer = models.ForeignKey(
        Importer,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="import_applications",
    )
    agent = models.ForeignKey(
        Importer,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="agent_import_applications",
    )
    importer_office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        blank=False,
        null=True,
        related_name="office_import_applications",
    )
    agent_office = models.ForeignKey(
        Office,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="agent_office_import_applications",
    )
    contact = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="contact_import_applications",
    )
    origin_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="import_applications_from",
    )
    consignment_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="import_applications_to",
    )
    variation_requests = models.ManyToManyField(VariationRequest)
    case_notes = models.ManyToManyField(CaseNote)
    further_information_requests = models.ManyToManyField(FurtherInformationRequest)
    update_requests = models.ManyToManyField(UpdateRequest)
    case_notes = models.ManyToManyField(CaseNote)
    commodity_group = models.ForeignKey(CommodityGroup, on_delete=models.PROTECT, null=True)
    case_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )
    cover_letter = models.TextField(blank=True, null=True)

    def get_workbasket_template(self):
        return "web/domains/workbasket/partials/import-case.html"

    @property
    def application_approved(self):
        return self.decision == self.APPROVE

    @property
    def licence_issue_date(self):
        return self.issue_date or timezone.now().date()


class ImportContact(models.Model):
    LEGAL = "legal"
    ENTITIES = (
        (LEGAL, "Legal Person"),
        ("natural", "Natural Person"),
    )
    DEALER_CHOICES = (
        ("yes", "Yes"),
        ("no", "No"),
    )

    import_application = models.ForeignKey(ImportApplication, on_delete=models.PROTECT)
    entity = models.CharField(max_length=10, choices=ENTITIES)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200, null=True, blank=True)
    registration_number = models.CharField(max_length=200, null=True, blank=True)
    street = models.CharField(max_length=200, verbose_name="Street and Number")
    city = models.CharField(max_length=200, verbose_name="Town/City")
    postcode = models.CharField(max_length=200, null=True, blank=True)
    region = models.CharField(max_length=200, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="+")
    dealer = models.CharField(max_length=10, choices=DEALER_CHOICES, null=True)

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class WithdrawImportApplication(models.Model):
    STATUS_OPEN = "open"
    STATUS_REJECTED = "rejected"
    STATUS_ACCEPTED = "accepted"

    OPEN = (STATUS_OPEN, "OPEN")
    REJECTED = (STATUS_REJECTED, "REJECTED")
    ACCEPTED = (STATUS_ACCEPTED, "ACCEPTED")
    STATUSES = (OPEN, REJECTED, ACCEPTED)

    import_application = models.ForeignKey(
        ImportApplication, on_delete=models.PROTECT, related_name="withdrawals"
    )
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUSES, default=STATUS_OPEN)
    reason = models.TextField()
    request_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="+",
    )

    response = models.TextField()
    response_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="+",
    )

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class EndorsementImportApplication(models.Model):
    import_application = models.ForeignKey(
        ImportApplication, on_delete=models.PROTECT, related_name="endorsements"
    )
    content = models.TextField()
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)
