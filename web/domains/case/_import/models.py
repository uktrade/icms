import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.indexes import BTreeIndex
from django.db import models
from django.urls import reverse

from web.domains.case.models import ApplicationBase, DocumentPackBase
from web.flow.models import ProcessTypes
from web.models.shared import EnumJsonEncoder, YesNoNAChoices
from web.types import TypedTextChoices


class ImportApplicationType(models.Model):
    class Types(TypedTextChoices):
        DEROGATION = ("SAN", "Derogation from Sanctions Import Ban")
        FIREARMS = ("FA", "Firearms and Ammunition")  # has subtypes
        IRON_STEEL = ("IS", "Iron and Steel (Quota)")
        OPT = ("OPT", "Outward Processing Trade")
        SANCTION_ADHOC = ("ADHOC", "Sanctions and Adhoc Licence Application")
        SPS = ("SPS", "Prior Surveillance")
        TEXTILES = ("TEX", "Textiles (Quota)")
        WOOD_QUOTA = ("WD", "Wood (Quota)")

    class SubTypes(TypedTextChoices):
        OIL = ("OIL", "Open Individual Import Licence")
        DFL = ("DEACTIVATED", "Deactivated Firearms Import Licence")
        SIL = ("SIL", "Specific Individual Import Licence")

    is_active = models.BooleanField(blank=False, null=False)
    type = models.CharField(max_length=70, blank=False, null=False, choices=Types.choices)
    sub_type = models.CharField(max_length=70, blank=True, null=True, choices=SubTypes.choices)
    name = models.CharField(max_length=100)
    licence_type_code = models.CharField(max_length=20, blank=False, null=False)
    sigl_flag = models.BooleanField(blank=False, null=False)
    chief_flag = models.BooleanField()
    chief_licence_prefix = models.CharField(max_length=10, blank=True, null=True)
    paper_licence_flag = models.BooleanField(blank=False, null=False)
    electronic_licence_flag = models.BooleanField(blank=False, null=False)
    cover_letter_flag = models.BooleanField(blank=False, null=False)
    cover_letter_schedule_flag = models.BooleanField(blank=False, null=False)
    category_flag = models.BooleanField(blank=False, null=False)
    sigl_category_prefix = models.CharField(max_length=100, blank=True, null=True)
    chief_category_prefix = models.CharField(max_length=10, blank=True, null=True)
    default_licence_length_months = models.IntegerField(blank=True, null=True)
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
        "web.CountryGroup",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="import_application_types_from",
    )
    consignment_country_group = models.ForeignKey(
        "web.CountryGroup",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="import_application_types_to",
    )
    master_country_group = models.ForeignKey(
        "web.CountryGroup",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="import_application_types",
    )
    commodity_type = models.ForeignKey(
        "web.CommodityType", on_delete=models.PROTECT, blank=True, null=True
    )
    declaration_template = models.ForeignKey(
        "web.Template",
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="declaration_application_types",
    )
    endorsements = models.ManyToManyField(
        "web.Template", related_name="endorsement_application_types"
    )
    default_commodity_group = models.ForeignKey(
        "web.CommodityGroup", on_delete=models.PROTECT, blank=True, null=True
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["type", "sub_type"],
                name="unique_import_app_type",
            )
        ]

    def _get_firearm_application_url(self) -> str:
        match self.sub_type:
            case self.SubTypes.OIL:
                return reverse("import:create-fa-oil")
            case self.SubTypes.DFL:
                return reverse("import:create-fa-dfl")
            case self.SubTypes.SIL:
                return reverse("import:create-fa-sil")
            case _:
                raise ValueError(
                    f"Unknown Firearms Application Sub Type: {self.sub_type}"  # /PS-IGNORE
                )

    @property
    def create_application_url(self) -> str:
        match self.type:
            case self.Types.FIREARMS:
                return self._get_firearm_application_url()
            case self.Types.WOOD_QUOTA:
                return reverse("import:create-wood-quota")
            case self.Types.DEROGATION:
                return reverse("import:create-derogations")
            case self.Types.IRON_STEEL:
                return reverse("import:create-ironsteel")
            case self.Types.OPT:
                return reverse("import:create-opt")
            case self.Types.SANCTION_ADHOC:
                return reverse("import:create-sanctions")
            case self.Types.TEXTILES:
                return reverse("import:create-textiles")
            case self.Types.SPS:
                return reverse("import:create-sps")
            case _:
                raise ValueError(f"Unknown Application Type: {self.type}")  # /PS-IGNORE


class ImportApplication(ApplicationBase):
    class ChiefUsageStatus(TypedTextChoices):
        CANCELLED = ("C", "Cancelled")
        EXHAUSTED = ("E", "Exhausted")  # Exhaustion Notified
        OPEN = ("O", "Open")
        SURRENDERED = ("S", "Surrendered")  # Surrender Notified (RPA only)
        EXPIRED = ("D", "Expired")  # Date expired

    class Meta:
        indexes = [
            models.Index(fields=["status"], name="IA_status_idx"),
            BTreeIndex(
                fields=["reference"],
                name="IA_search_case_reference_idx",
                opclasses=["text_pattern_ops"],
            ),
            models.Index(
                models.Q(submit_datetime__isnull=False), name="IA_submit_datetime_notnull_idx"
            ),
        ]

    applicant_reference = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Applicant's Reference",
        help_text="Enter your own reference for this application.",
    )

    create_datetime = models.DateTimeField(blank=False, null=False, auto_now_add=True)
    legacy_case_flag = models.BooleanField(blank=False, null=False, default=False)

    chief_usage_status = models.CharField(max_length=1, choices=ChiefUsageStatus.choices, null=True)

    variation_decision = models.CharField(
        max_length=10,
        choices=ApplicationBase.DECISIONS,
        null=True,
        verbose_name="Variation Decision",
    )
    variation_refuse_reason = models.CharField(
        max_length=4000, blank=True, null=True, verbose_name="Variation Refusal Reason"
    )

    licence_extended_flag = models.BooleanField(blank=False, null=False, default=False)

    licence_reference = models.OneToOneField(
        "web.UniqueReference", on_delete=models.PROTECT, related_name="+", null=True
    )

    last_update_datetime = models.DateTimeField(blank=False, null=False, auto_now=True)

    application_type = models.ForeignKey(
        "web.ImportApplicationType", on_delete=models.PROTECT, blank=False, null=False
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="submitted_import_applications",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="created_import_applications",
    )

    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="updated_import_cases",
    )

    importer = models.ForeignKey(
        "web.Importer", on_delete=models.PROTECT, related_name="import_applications"
    )

    agent = models.ForeignKey("web.Importer", on_delete=models.PROTECT, null=True, related_name="+")

    importer_office = models.ForeignKey(
        "web.Office", on_delete=models.PROTECT, null=True, related_name="+"
    )

    agent_office = models.ForeignKey(
        "web.Office", on_delete=models.PROTECT, null=True, related_name="+"
    )

    contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="contact_import_applications",
        help_text=(
            "Select the main point of contact for the case. This will usually be the person"
            " who created the application."
        ),
    )

    origin_country = models.ForeignKey(
        "web.Country",
        on_delete=models.PROTECT,
        null=True,
        related_name="import_applications_from",
        verbose_name="Country Of Origin",
        help_text="Select the country where the goods were made.",
    )

    consignment_country = models.ForeignKey(
        "web.Country",
        on_delete=models.PROTECT,
        null=True,
        related_name="import_applications_to",
        verbose_name="Country Of Consignment",
        help_text="Select the country where the goods were shipped from.",
    )

    variation_requests = models.ManyToManyField("web.VariationRequest")
    further_information_requests = models.ManyToManyField("web.FurtherInformationRequest")
    update_requests = models.ManyToManyField("web.UpdateRequest")
    case_notes = models.ManyToManyField("web.CaseNote")
    commodity_group = models.ForeignKey("web.CommodityGroup", on_delete=models.PROTECT, null=True)
    case_emails = models.ManyToManyField("web.CaseEmail", related_name="+")
    sigl_transmissions = models.ManyToManyField("web.SIGLTransmission")

    case_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )

    cover_letter_text = models.TextField(blank=True, null=True)

    # Only relevant to FA-SIL firearms applications
    imi_submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        verbose_name="IMI Submitter",
    )

    imi_submit_datetime = models.DateTimeField(null=True, verbose_name="Date provided to IMI")

    # Used in workbasket to clear applications
    cleared_by = models.ManyToManyField("web.User")

    def is_import_application(self) -> bool:
        return True

    def get_edit_view_name(self) -> str:
        if self.process_type == ProcessTypes.FA_OIL:
            return "import:fa-oil:edit"
        elif self.process_type == ProcessTypes.FA_DFL:
            return "import:fa-dfl:edit"
        elif self.process_type == ProcessTypes.FA_SIL:
            return "import:fa-sil:edit"
        elif self.process_type == ProcessTypes.OPT:
            return "import:opt:edit"
        elif self.process_type == ProcessTypes.DEROGATIONS:
            return "import:derogations:edit"
        elif self.process_type == ProcessTypes.SANCTIONS:
            return "import:sanctions:edit"
        elif self.process_type == ProcessTypes.WOOD:
            return "import:wood:edit"
        elif self.process_type == ProcessTypes.TEXTILES:
            return "import:textiles:edit"
        elif self.process_type == ProcessTypes.SPS:
            return "import:sps:edit"
        elif self.process_type == ProcessTypes.IRON_STEEL:
            return "import:ironsteel:edit"
        else:
            raise NotImplementedError(f"Unknown process_type {self.process_type}")

    def get_submit_view_name(self) -> str:
        if self.process_type == ProcessTypes.FA_OIL:
            return "import:fa-oil:submit-oil"
        elif self.process_type == ProcessTypes.FA_DFL:
            return "import:fa-dfl:submit"
        elif self.process_type == ProcessTypes.FA_SIL:
            return "import:fa-sil:submit"
        elif self.process_type == ProcessTypes.OPT:
            return "import:opt:submit"
        elif self.process_type == ProcessTypes.DEROGATIONS:
            return "import:derogations:submit-derogations"
        elif self.process_type == ProcessTypes.SANCTIONS:
            return "import:sanctions:submit-sanctions"
        elif self.process_type == ProcessTypes.WOOD:
            return "import:wood:submit-quota"
        elif self.process_type == ProcessTypes.TEXTILES:
            return "import:textiles:submit"
        elif self.process_type == ProcessTypes.SPS:
            return "import:sps:submit"
        elif self.process_type == ProcessTypes.IRON_STEEL:
            return "import:ironsteel:submit"
        else:
            raise NotImplementedError(f"Unknown process_type {self.process_type}")

    @property
    def application_approved(self):
        return self.decision == self.APPROVE

    def get_specific_model(self) -> "ImportApplication":
        return super().get_specific_model()

    def get_status_display(self) -> str:
        status = super().get_status_display()
        if self.decision == self.REFUSE:
            return f"{status} (Refused)"
        return status


class EndorsementImportApplication(models.Model):
    import_application = models.ForeignKey(
        "web.ImportApplication", on_delete=models.PROTECT, related_name="endorsements"
    )
    content = models.TextField()
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class ChecklistBase(models.Model):
    class Meta:
        abstract = True

    case_update = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Case update required from applicant?",
    )

    fir_required = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Further information request required?",
    )

    response_preparation = models.BooleanField(
        default=False,
        verbose_name="Response Preparation - approve/refuse the request, edit details if necessary",
    )

    validity_period_correct = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Validity period correct?",
    )

    endorsements_listed = models.CharField(
        max_length=3,
        choices=YesNoNAChoices.choices,
        null=True,
        verbose_name="Correct endorsements listed? Add/edit/remove as required (changes are automatically saved)",
    )

    authorisation = models.BooleanField(
        default=False,
        verbose_name="Authorisation - start authorisation (close case processing) to authorise the licence. Errors logged must be resolved.",
    )


class ImportApplicationLicence(DocumentPackBase):
    import_application = models.ForeignKey(
        "ImportApplication", on_delete=models.CASCADE, related_name="licences"
    )

    # A nullable boolean field that is either hardcoded or left to the user to
    # set later depending on the application type.
    issue_paper_licence_only = models.BooleanField(
        blank=False, null=True, verbose_name="Issue paper licence only?"
    )

    # Values set by ilb admin indicating when the licence starts / ends
    licence_start_date = models.DateField(verbose_name="Start Date", null=True)
    licence_end_date = models.DateField(verbose_name="End Date", null=True)

    # Set when licence is marked active.
    case_completion_datetime = models.DateTimeField(verbose_name="Case Completion Date", null=True)

    # Used in workbasket to clear licences
    cleared_by = models.ManyToManyField("web.User")
    document_references = GenericRelation(
        "CaseDocumentReference", related_query_name="import_application_licences"
    )

    def __str__(self):
        ia_pk = self.import_application_id
        st = self.status
        cr = self.case_reference
        ca = self.created_at

        return (
            f"ImportApplicationLicence("
            f"import_application={ia_pk}, status={st}, case_reference={cr}, created_at={ca}"
            f")"
        )


class ICMSHMRCChiefRequest(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["import_application", "case_reference", "request_sent_datetime"],
                name="app_reference_sent_at_unique",
            )
        ]

    class CHIEFStatus(TypedTextChoices):
        PROCESSING = ("P", "With CHIEF (Pending)")
        SUCCESS = ("S", "CHIEF Success")
        ERROR = ("E", "CHIEF Error")
        INTERNAL_ERROR = ("I", "Internal error sending data to CHIEF")

    import_application = models.ForeignKey(
        "ImportApplication", on_delete=models.CASCADE, related_name="chief_references"
    )
    case_reference = models.CharField(max_length=100, verbose_name="Case Reference")
    icms_hmrc_id = models.UUIDField(default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=1, choices=CHIEFStatus.choices, default=CHIEFStatus.PROCESSING
    )

    # ------------- CHIEF Request fields --------------
    request_data = models.JSONField(default=dict, encoder=EnumJsonEncoder)
    request_sent_datetime = models.DateTimeField()

    # ------------- CHIEF Response fields -------------
    response_received_datetime = models.DateTimeField(null=True)


class ChiefRequestResponseErrors(models.Model):
    request = models.ForeignKey(
        "web.ICMSHMRCChiefRequest", on_delete=models.PROTECT, related_name="response_errors"
    )
    error_code = models.CharField(null=True, max_length=8)
    error_msg = models.CharField(null=True, max_length=255)
