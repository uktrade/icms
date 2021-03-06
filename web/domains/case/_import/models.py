from django.db import models

from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import CaseNote, UpdateRequest, VariationRequest
from web.domains.commodity.models import CommodityGroup, CommodityType
from web.domains.constabulary.models import Constabulary
from web.domains.country.models import Country, CountryGroup
from web.domains.file.models import File
from web.domains.firearms.models import FirearmsAuthority
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.template.models import Template
from web.domains.user.models import User
from web.domains.workbasket.base import WorkbasketBase
from web.flow.models import Process


class ImportApplicationType(models.Model):
    TYPE_FIREARMS_AMMUNITION_CODE = "FA"
    TYPE = ((TYPE_FIREARMS_AMMUNITION_CODE, "Firearms and Ammunition"),)

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
        null=False,
        related_name="declaration_application_types",
    )
    endorsements = models.ManyToManyField(Template, related_name="endorsement_application_types")
    default_commodity_group = models.ForeignKey(
        CommodityGroup, on_delete=models.PROTECT, blank=True, null=True
    )

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
    DECISIONS = ((REFUSE, "Refuse"), (APPROVE, "Approve"))

    status = models.CharField(
        max_length=30, choices=STATUSES, blank=False, null=False, default=IN_PROGRESS
    )
    reference = models.CharField(max_length=50, blank=True, null=True)
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

    def get_workbasket_template(self):
        return "web/domains/workbasket/partials/import-case.html"


class OpenIndividualLicenceApplication(ImportApplication):
    PROCESS_TYPE = "OpenIndividualLicenceApplication"

    YES = "yes"
    NO = "no"
    KNOW_BOUGHT_FROM_CHOICES = (
        (YES, "Yes"),
        (NO, "No"),
    )

    section1 = models.BooleanField(verbose_name="Section 1", default=True)
    section2 = models.BooleanField(verbose_name="Section 2", default=True)
    know_bought_from = models.CharField(max_length=10, choices=KNOW_BOUGHT_FROM_CHOICES, null=True)


class ConstabularyEmail(models.Model):

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    DRAFT = "DRAFT"
    STATUSES = ((OPEN, "Open"), (CLOSED, "Closed"), (DRAFT, "Draft"))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    application = models.ForeignKey(
        ImportApplication, on_delete=models.PROTECT, blank=False, null=False
    )
    status = models.CharField(max_length=30, blank=False, null=False, default=DRAFT)
    email_cc_address_list = models.CharField(max_length=4000, blank=True, null=True)
    email_subject = models.CharField(max_length=100, blank=False, null=True)
    email_body = models.TextField(max_length=4000, blank=False, null=True)
    email_response = models.TextField(max_length=4000, blank=True, null=True)
    email_sent_datetime = models.DateTimeField(blank=True, null=True)
    email_closed_datetime = models.DateTimeField(blank=True, null=True)


class UserImportCertificate(models.Model):
    REGISTERED_KEY = "registered"
    REGISTERED_TEXT = "Registered Firearms Dealer Certificate"
    REGISTERED = (REGISTERED_KEY, REGISTERED_TEXT)
    CERTIFICATE_TYPE = (
        ("firearms", "Firearms Certificate"),
        REGISTERED,
        ("shotgun", "Shotgun Certificate"),
    )

    import_application = models.ForeignKey(ImportApplication, on_delete=models.PROTECT)
    reference = models.CharField(verbose_name="Certificate Reference", max_length=200)
    certificate_type = models.CharField(
        verbose_name="Certificate Type", choices=CERTIFICATE_TYPE, max_length=200
    )
    constabulary = models.ForeignKey(Constabulary, on_delete=models.PROTECT)
    date_issued = models.DateField(verbose_name="Date Issued")
    expiry_date = models.DateField(verbose_name="Expiry Date")
    files = models.ManyToManyField(File)

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class VerifiedCertificate(models.Model):
    import_application = models.ForeignKey(
        ImportApplication, on_delete=models.PROTECT, related_name="verified_certificates"
    )
    firearms_authority = models.ForeignKey(
        FirearmsAuthority, on_delete=models.PROTECT, related_name="+"
    )

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)


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
