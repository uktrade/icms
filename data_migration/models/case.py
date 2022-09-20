from typing import Any, Generator

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import F, OuterRef, QuerySet, Subquery, Value
from django.db.models.expressions import Window
from django.db.models.functions import RowNumber

from data_migration.models.export_application.export import ExportApplication
from data_migration.utils.format import str_to_list

from .base import MigrationBase
from .export_application import ExportApplicationCertificate, GMPBrand
from .file import DocFolder, File, FileFolder
from .flow import Process
from .import_application import ImportApplication, ImportApplicationLicence
from .reference import Country
from .user import User


class CaseReference(MigrationBase):
    prefix = models.CharField(max_length=8)
    year = models.IntegerField(null=True)
    reference = models.IntegerField()


class CaseDocument(MigrationBase):
    licence = models.ForeignKey(
        ImportApplicationLicence, on_delete=models.CASCADE, to_field="imad_id", null=True
    )
    cad = models.ForeignKey(
        ExportApplicationCertificate, on_delete=models.CASCADE, to_field="cad_id", null=True
    )
    certificate_id = models.PositiveIntegerField(null=True, unique=True)
    document_legacy = models.OneToOneField(
        File, on_delete=models.SET_NULL, null=True, to_field="document_legacy_id"
    )
    document_type = models.CharField(max_length=12)
    reference = models.CharField(max_length=20, null=True)

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["File", cls.__name__]

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + [
            "licence_id",
            "cad_id",
            "document_legacy_id",
            "casedocument_ptr_id",
            "certificate_id",
        ]

    @classmethod
    def exclude_kwargs(cls) -> dict[str, Any]:
        return {}

    @classmethod
    def get_source_data(cls) -> Generator:
        exclude_kwargs = cls.exclude_kwargs()
        values = cls.get_values()
        values_kwargs = cls.get_values_kwargs()

        return (
            CaseDocument.objects.exclude(**exclude_kwargs)
            .values(*values, **values_kwargs)
            .iterator()
        )


class ImportCaseDocument(CaseDocument):
    class Meta:
        abstract = True

    @classmethod
    def exclude_kwargs(cls) -> dict[str, Any]:
        return {"licence__isnull": True}

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        content_type_id = ContentType.objects.get(
            app_label="web", model="importapplicationlicence"
        ).id

        return {
            "object_id": F("licence__pk"),
            "document_id": F("document_legacy__pk"),
            "content_type_id": Value(content_type_id),
        }


class ExportCaseDocument(CaseDocument):
    class Meta:
        abstract = True

    @classmethod
    def exclude_kwargs(cls) -> dict[str, Any]:
        return {"cad__isnull": True}

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        content_type_id = ContentType.objects.get(
            app_label="web", model="exportapplicationcertificate"
        ).id

        return {
            "object_id": F("cad__pk"),
            "document_id": F("document_legacy__pk"),
            "content_type_id": Value(content_type_id),
        }


class ExportCertificateCaseDocumentReferenceData(MigrationBase):
    certificate = models.OneToOneField(
        CaseDocument, on_delete=models.CASCADE, to_field="certificate_id"
    )
    country = models.ForeignKey(Country, on_delete=models.PROTECT)

    @classmethod
    def get_source_data(cls) -> Generator:
        sub_query = GMPBrand.objects.filter(cad_id=OuterRef("certificate__cad_id")).values("pk")

        values = cls.get_values()
        values_kwargs = cls.get_values_kwargs()

        return (
            cls.objects.annotate(gmp_brand_id=Subquery(sub_query[:1]))
            .values("gmp_brand_id", *values, **values_kwargs)
            .iterator()
        )

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["File", "CaseDocument", cls.__name__]

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["certificate_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"case_document_reference_id": F("certificate__id")}


class VariationRequest(MigrationBase):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.SET_NULL, null=True)
    ca = models.ForeignKey(Process, on_delete=models.CASCADE, null=True, to_field="ca_id")
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=30)
    extension_flag = models.BooleanField(default=False)
    requested_datetime = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    what_varied = models.CharField(max_length=4000)
    why_varied = models.CharField(max_length=4000, null=True)
    when_varied = models.DateField(null=True)
    reject_cancellation_reason = models.CharField(max_length=4000, null=True)
    update_request_reason = models.CharField(max_length=4000, null=True)
    closed_datetime = models.DateTimeField(null=True)
    closed_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["import_application_id", "ca_id"]

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        target_name = target._meta.model_name

        if target_name == "exportapplication":
            return (
                cls.objects.exclude(ca__isnull=True)
                .values("id", variationrequest_id=F("id"), exportapplication_id=F("ca__id"))
                .iterator()
            )

        return (
            cls.objects.exclude(import_application__isnull=True)
            .values(
                "id", variationrequest_id=F("id"), importapplication_id=F("import_application__id")
            )
            .iterator()
        )


class CaseEmail(MigrationBase):
    ima = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        to_field="ima_id",
        null=True,
        related_name="ia_caseemails",
    )
    ca = models.ForeignKey(
        Process, on_delete=models.CASCADE, to_field="ca_id", null=True, related_name="ea_caseemails"
    )
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=30)
    to = models.EmailField(max_length=254, null=True)
    cc_address_list_str = models.TextField(max_length=4000, null=True)
    subject = models.CharField(max_length=100, null=True)
    body = models.TextField(max_length=4000, null=True)
    response = models.TextField(max_length=4000, null=True)
    sent_datetime = models.DateTimeField(null=True)
    closed_datetime = models.DateTimeField(null=True)

    # attachments - M2M to file

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["ima_id", "ca_id"]

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        address_list_str = data.pop("cc_address_list_str") or ""
        data["cc_address_list"] = str_to_list(address_list_str)

        return data

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        target_name = target._meta.model_name

        if target_name == "exportapplication":
            return (
                cls.objects.exclude(ca__isnull=True)
                .values("id", caseemail_id=F("id"), exportapplication_id=F("ca__id"))
                .iterator()
            )

        return (
            cls.objects.select_related("ima")
            .values("id", importapplication_id=F("ima__id"), caseemail_id=F("id"))
            .iterator()
        )


class CaseNote(MigrationBase):
    ima = models.ForeignKey(Process, on_delete=models.CASCADE, to_field="ima_id", null=True)
    export_application = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(null=False, default=True)
    status = models.CharField(max_length=20, null=False, default="DRAFT")
    note = models.TextField(null=True)
    create_datetime = models.DateTimeField(null=False, auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=False)
    file_folder = models.OneToOneField(
        FileFolder,
        on_delete=models.CASCADE,
        related_name="case_note",
        null=True,
    )
    doc_folder = models.OneToOneField(
        DocFolder,
        on_delete=models.CASCADE,
        related_name="case_note",
        null=True,
    )

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + [
            "ima_id",
            "export_application_id",
            "file_folder_id",
            "doc_folder_id",
        ]

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        target_name = target._meta.model_name

        if target_name == "exportapplication":
            return (
                cls.objects.exclude(export_application__isnull=True)
                .values("id", exportapplication_id=F("export_application_id"), casenote_id=F("id"))
                .iterator()
            )

        return (
            cls.objects.select_related("ima")
            .exclude(ima__isnull=True)
            .values("id", importapplication_id=F("ima__id"), casenote_id=F("id"))
            .iterator()
        )


class CaseNoteFile(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = data.pop("row_number") + data.pop("start")
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        ia_case_note_qs = (
            File.objects.select_related("target__folder__case_note__pk")
            .filter(target__folder__case_note__isnull=False)
            .annotate(row_number=Window(expression=RowNumber()))
            .values(
                "row_number",
                start=Value(0, output_field=models.IntegerField()),
                file_id=F("pk"),
                casenote_id=F("target__folder__case_note__pk"),
            )
        )

        ea_start = ia_case_note_qs.count()
        ea_case_note_qs = (
            File.objects.select_related("doc_folder__case_note__pk")
            .filter(doc_folder__case_note__isnull=False)
            .annotate(row_number=Window(expression=RowNumber()))
            .values(
                "row_number",
                start=Value(ea_start, output_field=models.IntegerField()),
                file_id=F("pk"),
                casenote_id=F("doc_folder__case_note__pk"),
            )
        )

        return QuerySet.union(ia_case_note_qs, ea_case_note_qs).iterator()


class UpdateRequest(MigrationBase):
    ima = models.ForeignKey(Process, on_delete=models.CASCADE, to_field="ima_id")
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=30)
    request_subject = models.CharField(max_length=100, null=True)
    request_detail = models.TextField(null=True)
    response_detail = models.TextField(null=True)
    request_datetime = models.DateTimeField(null=True)
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    response_datetime = models.DateTimeField(null=True)
    response_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    closed_datetime = models.DateTimeField(null=True)
    closed_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["ima_id"]

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        return (
            cls.objects.select_related("ima")
            .values("id", importapplication_id=F("ima__id"), updaterequest_id=F("id"))
            .iterator()
        )


class FurtherInformationRequest(MigrationBase):
    PROCESS_PK = True

    ia_ima = models.ForeignKey(Process, on_delete=models.CASCADE, to_field="ima_id")
    status = models.CharField(max_length=20)
    request_subject = models.CharField(max_length=100, null=True)
    request_detail = models.TextField(null=True)
    email_cc_address_list_str = models.TextField(max_length=4000, null=True)
    requested_datetime = models.DateTimeField(null=True, auto_now_add=True)
    response_detail = models.CharField(max_length=4000, null=True)
    response_datetime = models.DateTimeField(null=True)
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    response_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    closed_datetime = models.DateTimeField(null=True)
    closed_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    deleted_datetime = models.DateTimeField(null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    folder = models.OneToOneField(
        FileFolder, on_delete=models.CASCADE, related_name="fir", null=True
    )

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", cls.__name__]

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["ia_ima_id", "folder_id"]

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        address_list_str = data.pop("email_cc_address_list_str") or ""
        data["email_cc_address_list"] = str_to_list(address_list_str)
        data["process_ptr_id"] = data.pop("id")

        return data

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        return (
            cls.objects.select_related("ia_ima")
            .values(
                "id", importapplication_id=F("ia_ima__id"), furtherinformationrequest_id=F("id")
            )
            .iterator()
        )


class FIRFile(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = data.pop("row_number")
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        return (
            File.objects.select_related("target__folder__fir_id")
            .filter(
                target__folder__folder_type="IMP_RFI_DOCUMENTS",
                target__folder__fir__isnull=False,
            )
            .annotate(row_number=Window(expression=RowNumber()))
            .values(
                "row_number",
                file_id=F("pk"),
                furtherinformationrequest_id=F("target__folder__fir__pk"),
            )
            .iterator()
        )


class Mailshot(MigrationBase):
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20)
    title = models.CharField(max_length=200, null=True)
    description = models.CharField(max_length=4000, null=True)
    is_email = models.BooleanField(default=True)
    email_subject = models.CharField(max_length=200)
    email_body = models.CharField(max_length=4000, null=True)
    is_retraction_email = models.BooleanField(default=True)
    retract_email_subject = models.CharField(max_length=78, null=True)
    retract_email_body = models.CharField(max_length=4000, null=True)
    is_to_importers = models.BooleanField(default=False)
    is_to_exporters = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    create_datetime = models.DateTimeField(auto_now_add=True)
    published_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    published_datetime = models.DateTimeField(null=True)
    retracted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    retracted_datetime = models.DateTimeField(null=True)
    reference = models.CharField(max_length=100, null=True)
    version = models.PositiveIntegerField(default=0)
    folder = models.OneToOneField(FileFolder, on_delete=models.CASCADE, related_name="mailshot")

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["folder_id"]


class MailshotDoc(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = data.pop("row_number")
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        return (
            File.objects.select_related("target__folder__mailshot_id")
            .filter(
                target__folder__folder_type="MAILSHOT_DOCUMENTS",
                target__folder__mailshot__isnull=False,
            )
            .annotate(row_number=Window(expression=RowNumber()))
            .values(
                "row_number",
                file_id=F("pk"),
                mailshot_id=F("target__folder__mailshot__pk"),
            )
            .iterator()
        )
