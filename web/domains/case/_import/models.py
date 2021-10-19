from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.postgres.indexes import BTreeIndex
from django.db import models
from django.urls import reverse
from django.utils import timezone
from guardian.shortcuts import get_users_with_perms

from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import (
    ApplicationBase,
    CaseEmail,
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
from web.domains.workbasket.base import WorkbasketAction, WorkbasketRow
from web.flow.models import ProcessTypes
from web.models.shared import YesNoNAChoices

if TYPE_CHECKING:
    from django.db.models import QuerySet


class ImportApplicationType(models.Model):
    class Types(models.TextChoices):
        DEROGATION = ("SAN", "Derogation from Sanctions Import Ban")
        FIREARMS = ("FA", "Firearms and Ammunition")  # has subtypes
        IRON_STEEL = ("IS", "Iron and Steel (Quota)")
        OPT = ("OPT", "Outward Processing Trade")
        SANCTION_ADHOC = ("ADHOC", "Sanctions and Adhoc Licence Application")
        SPS = ("SPS", "Prior Surveillance")
        TEXTILES = ("TEX", "Textiles (Quota)")
        WOOD_QUOTA = ("WD", "Wood (Quota)")

    class SubTypes(models.TextChoices):
        OIL = ("OIL", "Open Individual Import Licence")
        DFL = ("DEACTIVATED", "Deactivated Firearms Import Licence")
        SIL = ("SIL", "Specific Individual Import Licence")

    is_active = models.BooleanField(blank=False, null=False)
    type = models.CharField(max_length=70, blank=False, null=False, choices=Types.choices)
    sub_type = models.CharField(max_length=70, blank=True, null=True, choices=SubTypes.choices)
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

    def __str__(self):
        mapped_types = {
            self.Types.DEROGATION: ProcessTypes.DEROGATIONS,
            self.Types.IRON_STEEL: ProcessTypes.IRON_STEEL,
            self.Types.OPT: ProcessTypes.OPT,
            self.Types.SANCTION_ADHOC: ProcessTypes.SANCTIONS,
            self.Types.SPS: ProcessTypes.SPS,
            self.Types.TEXTILES: ProcessTypes.TEXTILES,
            self.Types.WOOD_QUOTA: ProcessTypes.WOOD,
        }

        mapped_types_with_subtypes = {
            self.Types.FIREARMS: {
                self.SubTypes.OIL: ProcessTypes.FA_OIL,
                self.SubTypes.DFL: ProcessTypes.FA_DFL,
                self.SubTypes.SIL: ProcessTypes.FA_SIL,
            }
        }

        if self.type in mapped_types.keys():
            process_type = mapped_types[self.type]

        elif self.type in mapped_types_with_subtypes.keys():
            process_type = mapped_types_with_subtypes[self.type][self.sub_type]

        else:
            raise NotImplementedError(f"Can't get label for {self.type}, {self.sub_type}")

        return ProcessTypes(process_type).label

    class Meta:
        ordering = ("type", "sub_type")


class ImportApplication(ApplicationBase):
    class ChiefUsageTypes(models.TextChoices):
        CANCELLED = ("C", "Cancelled")
        EXHAUSTED = ("E", "Exhausted")
        EXPIRED = ("D", "Expired")
        SURRENDERED = ("S", "Surrendered")

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
    variation_no = models.IntegerField(blank=False, null=False, default=0)
    legacy_case_flag = models.BooleanField(blank=False, null=False, default=False)

    chief_usage_status = models.CharField(max_length=1, choices=ChiefUsageTypes.choices, null=True)

    under_appeal_flag = models.BooleanField(blank=False, null=False, default=False)

    variation_decision = models.CharField(
        max_length=10, choices=ApplicationBase.DECISIONS, blank=True, null=True
    )

    variation_refuse_reason = models.CharField(max_length=4000, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    licence_start_date = models.DateField(blank=True, null=True)
    licence_end_date = models.DateField(blank=True, null=True)
    licence_extended_flag = models.BooleanField(blank=False, null=False, default=False)

    # TODO: Revisit when implementing ICMSLST-1048
    # See def submit_application in ApplicationBase regarding making this unique
    licence_reference = models.CharField(max_length=100, null=True, unique=True)

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
        Importer, on_delete=models.PROTECT, related_name="import_applications"
    )

    agent = models.ForeignKey(Importer, on_delete=models.PROTECT, null=True, related_name="+")

    importer_office = models.ForeignKey(
        Office, on_delete=models.PROTECT, null=True, related_name="+"
    )

    agent_office = models.ForeignKey(Office, on_delete=models.PROTECT, null=True, related_name="+")

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
        help_text="Select the country where the goods were made.",
    )

    consignment_country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        null=True,
        related_name="import_applications_to",
        verbose_name="Country Of Consignment",
        help_text="Select the country where the goods were shipped from.",
    )

    variation_requests = models.ManyToManyField(VariationRequest)
    further_information_requests = models.ManyToManyField(FurtherInformationRequest)
    update_requests = models.ManyToManyField(UpdateRequest)
    case_notes = models.ManyToManyField(CaseNote)
    commodity_group = models.ForeignKey(CommodityGroup, on_delete=models.PROTECT, null=True)
    case_emails = models.ManyToManyField(CaseEmail, related_name="+")

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

    # Only relevant to firearms applications
    imi_submitted_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, related_name="+", verbose_name="IMI Submitter"
    )

    imi_submit_datetime = models.DateTimeField(null=True, verbose_name="Date provided to IMI")

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

    def user_is_contact_of_org(self, user: User) -> bool:
        return user.has_perm("web.is_contact_of_importer", self.importer)

    def user_is_agent_of_org(self, user: User) -> bool:
        return user.has_perm("web.is_agent_of_importer", self.importer)

    def get_org_contacts(self) -> "QuerySet[User]":
        return get_users_with_perms(self.importer, only_with_perms_in=["is_contact_of_importer"])

    def get_agent_contacts(self) -> "QuerySet[User]":
        return get_users_with_perms(self.agent, only_with_perms_in=["is_contact_of_importer"])

    def get_workbasket_subject(self) -> str:
        return "\n".join(["Import Application", ProcessTypes(self.process_type).label])

    def get_workbasket_row(self, user: User) -> WorkbasketRow:
        r = super().get_workbasket_row(user)

        is_importer_user = user.has_perm("web.importer_access")
        include_importer_rows = is_importer_user or settings.DEBUG_SHOW_ALL_WORKBASKET_ROWS

        if include_importer_rows:
            importer_actions = self._get_importer_actions()

            if importer_actions:
                r.actions.append(importer_actions)

        return r

    def _get_importer_actions(self):
        importer_actions: list[WorkbasketAction] = []

        if (
            self.status == self.Statuses.COMPLETED
            and self.application_type.type == ImportApplicationType.Types.FIREARMS
        ):
            importer_actions.append(
                WorkbasketAction(
                    is_post=False,
                    name="Provide Report",
                    url=reverse("import:fa:provide-report", kwargs={"application_pk": self.pk}),
                ),
            )

        return importer_actions

    @property
    def application_approved(self):
        return self.decision == self.APPROVE

    @property
    def licence_issue_date(self):
        # NOTE: This field is never set but is used in two places
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
