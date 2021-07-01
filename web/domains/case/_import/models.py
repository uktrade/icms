from django.db import models
from django.utils import timezone

from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import (
    ApplicationBase,
    CaseNote,
    UpdateRequest,
    VariationRequest,
)
from web.domains.commodity.models import CommodityGroup, CommodityType
from web.domains.country.models import Country, CountryGroup
from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.domains.template.models import Template
from web.domains.user.models import User
from web.models.shared import YesNoNAChoices


class ImportApplicationType(models.Model):
    class Types(models.TextChoices):
        FIREARMS = ("FA", "Firearms and Ammunition")
        DEROGATION = ("SAN", "Derogation from Sanctions Import Ban")
        # TODO: missing from legacy data extract, hence TEMP
        SANCTION_ADHOC = ("SAN_ADHOC_TEMP", "Sanctions and Adhoc")
        WOOD_QUOTA = ("WD", "Wood (Quota)")
        OPT = ("OPT", "Outward Processing Trade")
        TEXTILES = ("TEX", "Textiles (Quota)")

    class SubTypes(models.TextChoices):
        OIL = ("OIL", "Open Individual Import Licence")
        DFL = ("DEACTIVATED", "Deactivated Firearms Import Licence")
        SIL = ("SIL", "Specific Import Licence")

    class ProcessTypes(models.TextChoices):
        FA_SIL = ("SILApplication", "Firearms and Ammunition (Specific Individual Import Licence)")
        FA_OIL = (
            "OpenIndividualLicenceApplication",
            "Firearms and Ammunition (Open Individual Import Licence)",
        )
        FA_DFL = ("DFLApplication", "Firearms and Ammunition (Deactivated Firearms Licence)")
        WOOD = ("WoodQuotaApplication", "Wood (Quota)")
        OPT = ("OutwardProcessingTradeApplication", "Outward Processing Trade")
        SANCTIONS = ("SanctionsAndAdhocApplication", "Sanctions and Adhoc Licence Application")
        DEROGATIONS = ("DerogationsApplication", "Derogation from Sanctions Import Ban")
        TEXTILES = ("TextilesApplication", "Textiles (Quota)")

    is_active = models.BooleanField(blank=False, null=False)
    type = models.CharField(max_length=70, blank=False, null=False, choices=Types.choices)
    sub_type = models.CharField(max_length=70, blank=True, null=True, choices=SubTypes.choices)
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


class ImportApplication(ApplicationBase):
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

    applicant_reference = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Applicant's Reference",
        help_text="Enter your own reference for this application.",
    )

    create_datetime = models.DateTimeField(blank=False, null=False, auto_now_add=True)
    variation_no = models.IntegerField(blank=False, null=False, default=0)
    legacy_case_flag = models.BooleanField(blank=False, null=False, default=False)

    chief_usage_status = models.CharField(
        max_length=1, choices=CHIEF_STATUSES, blank=True, null=True
    )

    under_appeal_flag = models.BooleanField(blank=False, null=False, default=False)

    variation_decision = models.CharField(
        max_length=10, choices=ApplicationBase.DECISIONS, blank=True, null=True
    )

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
        null=True,
        related_name="contact_import_applications",
        help_text=(
            "Select the main point of contact for the case. This will usually be the person"
            " who created the application."
        ),
    )

    origin_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        related_name="import_applications_from",
        verbose_name="Country Of Origin",
    )

    consignment_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        related_name="import_applications_to",
        verbose_name="Country Of Consignment",
    )

    variation_requests = models.ManyToManyField(VariationRequest)
    further_information_requests = models.ManyToManyField(FurtherInformationRequest)
    update_requests = models.ManyToManyField(UpdateRequest)
    case_notes = models.ManyToManyField(CaseNote)
    commodity_group = models.ForeignKey(CommodityGroup, on_delete=models.PROTECT, null=True)

    case_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )

    cover_letter = models.TextField(blank=True, null=True)

    # A nullable boolean field that is either hardcoded or left to the user to
    # set later depending on the application type.
    issue_paper_licence_only = models.BooleanField(
        blank=False,
        null=True,
        verbose_name="Issue paper licence only?",
    )

    def is_import_application(self) -> bool:
        return True

    def get_edit_view_name(self) -> str:
        if self.process_type == ImportApplicationType.ProcessTypes.FA_OIL:
            return "import:fa-oil:edit"
        elif self.process_type == ImportApplicationType.ProcessTypes.FA_DFL:
            return "import:fa-dfl:edit"
        elif self.process_type == ImportApplicationType.ProcessTypes.FA_SIL:
            return "import:fa-sil:edit"
        elif self.process_type == ImportApplicationType.ProcessTypes.OPT:
            return "import:opt:edit"
        elif self.process_type == ImportApplicationType.ProcessTypes.DEROGATIONS:
            return "import:derogations:edit"
        elif self.process_type == ImportApplicationType.ProcessTypes.SANCTIONS:
            return "import:sanctions:edit"
        elif self.process_type == ImportApplicationType.ProcessTypes.WOOD:
            return "import:wood:edit"
        elif self.process_type == ImportApplicationType.ProcessTypes.TEXTILES:
            return "import:textiles:edit"
        else:
            raise NotImplementedError(f"Unknown process_type {self.process_type}")

    def user_is_contact_of_org(self, user: User) -> bool:
        return user.has_perm("web.is_contact_of_importer", self.importer)

    def get_workbasket_subject(self) -> str:
        return "\n".join(
            [
                "Import Application",
                ImportApplicationType.ProcessTypes(self.process_type).label,
            ]
        )

    @property
    def application_approved(self):
        return self.decision == self.APPROVE

    @property
    def licence_issue_date(self):
        return self.issue_date or timezone.now().date()


class EndorsementImportApplication(models.Model):
    import_application = models.ForeignKey(
        ImportApplication, on_delete=models.PROTECT, related_name="endorsements"
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
