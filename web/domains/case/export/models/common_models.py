from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.indexes import BTreeIndex
from django.db import models
from django.urls import reverse

from web.domains.case.models import ApplicationBase, DocumentPackBase
from web.flow.models import ProcessTypes
from web.types import TypedTextChoices


class ExportApplicationType(models.Model):
    class Types(TypedTextChoices):
        FREE_SALE = ("CFS", "Certificate of Free Sale")
        MANUFACTURE = ("COM", "Certificate of Manufacture")
        GMP = ("GMP", "Certificate of Good Manufacturing Practice")

    is_active = models.BooleanField(blank=False, null=False, default=True)

    # TODO ICMSLST-2085: Change this to type to match ImportApplication
    type_code = models.CharField(
        max_length=30, blank=False, null=False, unique=True, choices=Types.choices
    )

    # TODO ICMSLST-2085: Change this to name to match ImportApplication
    type = models.CharField(max_length=70, blank=False, null=False)

    allow_multiple_products = models.BooleanField(blank=False, null=False)
    generate_cover_letter = models.BooleanField(blank=False, null=False)
    allow_hse_authorization = models.BooleanField(blank=False, null=False)
    country_group = models.ForeignKey(
        "web.CountryGroup", on_delete=models.PROTECT, blank=False, null=False
    )
    country_group_for_manufacture = models.ForeignKey(
        "web.CountryGroup",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="manufacture_export_application_types",
    )

    def __str__(self):
        return f"{self.type}"

    class Meta:
        ordering = ("type",)

    @property
    def create_application_url(self) -> str:
        match self.type_code:
            case self.Types.FREE_SALE:
                return reverse("export:create-application", kwargs={"type_code": "cfs"})
            case self.Types.MANUFACTURE:
                return reverse("export:create-application", kwargs={"type_code": "com"})
            case self.Types.GMP:
                return reverse("export:create-application", kwargs={"type_code": "gmp"})
            case _:
                raise ValueError(f"Unknown Application Type: {self.type_code}")  # /PS-IGNORE


class ExportApplicationABC(models.Model):
    """Base class for ExportApplication and the templates."""

    class Meta:
        abstract = True

    last_update_datetime = models.DateTimeField(blank=False, null=False, auto_now=True)
    variation_no = models.IntegerField(blank=False, null=False, default=0)

    countries = models.ManyToManyField(
        "web.Country",
        help_text=(
            "A certificate will be created for each country selected. You may"
            " select up to 40 countries. You cannot select the same country"
            " twice, you must submit a new application."
        ),
    )

    def is_import_application(self) -> bool:
        return False


class ExportApplication(ExportApplicationABC, ApplicationBase):
    class Meta:
        indexes = [
            models.Index(fields=["status"], name="EA_status_idx"),
            BTreeIndex(
                fields=["reference"],
                name="EA_search_case_reference_idx",
                opclasses=["text_pattern_ops"],
            ),
            models.Index(fields=["-submit_datetime"], name="EA_submit_datetime_idx"),
        ]

    application_type = models.ForeignKey(
        "web.ExportApplicationType", on_delete=models.PROTECT, blank=False, null=False
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="updated_export_cases",
    )

    variation_requests = models.ManyToManyField("web.VariationRequest")
    case_notes = models.ManyToManyField("web.CaseNote")
    further_information_requests = models.ManyToManyField("web.FurtherInformationRequest")
    update_requests = models.ManyToManyField("web.UpdateRequest")
    case_emails = models.ManyToManyField("web.CaseEmail", related_name="+")

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="submitted_export_application",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="created_export_applications",
    )

    exporter = models.ForeignKey("web.Exporter", on_delete=models.PROTECT, related_name="+")

    exporter_office = models.ForeignKey(
        "web.Office", on_delete=models.PROTECT, null=True, related_name="+"
    )

    contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="contact_export_applications",
        help_text=(
            "Select the main point of contact for the case. This will usually"
            " be the person who created the application."
        ),
    )

    agent = models.ForeignKey("web.Exporter", on_delete=models.PROTECT, null=True, related_name="+")
    agent_office = models.ForeignKey(
        "web.Office", on_delete=models.PROTECT, null=True, related_name="+"
    )

    case_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )

    # Used in workbasket to clear applications
    cleared_by = models.ManyToManyField("web.User")

    def get_edit_view_name(self) -> str:
        if self.process_type == ProcessTypes.COM:
            return "export:com-edit"
        if self.process_type == ProcessTypes.CFS:
            return "export:cfs-edit"
        if self.process_type == ProcessTypes.GMP:
            return "export:gmp-edit"
        else:
            raise NotImplementedError(f"Unknown process_type {self.process_type}")

    def get_submit_view_name(self) -> str:
        if self.process_type == ProcessTypes.COM:
            return "export:com-submit"
        if self.process_type == ProcessTypes.CFS:
            return "export:cfs-submit"
        if self.process_type == ProcessTypes.GMP:
            return "export:gmp-submit"
        else:
            raise NotImplementedError(f"Unknown process_type {self.process_type}")

    def get_specific_model(self) -> "ExportApplication":
        return super().get_specific_model()

    def get_status_display(self) -> str:
        # Export applications have a different label for Variation Requested
        status = super().get_status_display()
        if self.status == self.Statuses.VARIATION_REQUESTED:
            return "Case Variation"
        if self.decision == self.REFUSE:
            return f"{status} (Refused)"
        return status

    @property
    def application_approved(self):
        return self.decision == self.APPROVE


class ExportApplicationCertificate(DocumentPackBase):
    export_application = models.ForeignKey(
        "ExportApplication", on_delete=models.CASCADE, related_name="certificates"
    )

    # Set when certificate is marked active.
    case_completion_datetime = models.DateTimeField(verbose_name="Issue Date", null=True)
    document_references = GenericRelation(
        "CaseDocumentReference", related_query_name="export_application_certificates"
    )
    # Used in workbasket to clear certificates
    cleared_by = models.ManyToManyField("web.User")

    def __str__(self):
        ea_pk, st, ca = (self.export_application_id, self.status, self.created_at)
        return f"ExportApplicationCertificate(export_application_id={ea_pk}, status={st}, created_at={ca})"


class ExportCertificateCaseDocumentReferenceData(models.Model):
    """Extra information needed for Export Application CaseDocumentReference.

    Export applications have multiple certificates.
    """

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["case_document_reference", "country"],
                name="cert_doc_ref_data_unique",
            )
        ]

    case_document_reference = models.OneToOneField(
        "web.CaseDocumentReference", on_delete=models.CASCADE, related_name="reference_data"
    )
    country = models.ForeignKey("web.Country", on_delete=models.PROTECT)

    def __str__(self):
        return (
            f"ExportCertificateCaseDocumentReferenceData("
            f"case_document_reference_id={self.case_document_reference_id}"
            f", country_id={self.country_id}"
            f")"
        )
