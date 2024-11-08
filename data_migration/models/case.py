from django.db import models

from data_migration.models.export_application.export import ExportApplication

from .base import MigrationBase
from .export_application import ExportApplicationCertificate
from .file import DocFolder, File, FileFolder, FileTarget
from .flow import Process
from .import_application import ImportApplication, ImportApplicationLicence
from .reference import Country
from .user import AccessRequest, User


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
    check_code = models.CharField(null=True, max_length=16)


class ExportCertificateCaseDocumentReferenceData(MigrationBase):
    certificate = models.OneToOneField(
        CaseDocument, on_delete=models.CASCADE, to_field="certificate_id"
    )
    country = models.ForeignKey(Country, on_delete=models.PROTECT)


class DocumentPackAcknowledgement(MigrationBase):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    importapplicationlicence = models.ForeignKey(
        ImportApplicationLicence,
        on_delete=models.CASCADE,
        to_field="document_pack_id",
        null=True,
        related_name="acknowledgements",
    )
    exportcertificate = models.ForeignKey(
        ExportApplicationCertificate,
        on_delete=models.CASCADE,
        to_field="document_pack_id",
        null=True,
        related_name="acknowledgements",
    )


class VariationRequest(MigrationBase):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.SET_NULL, null=True)
    export_application = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=30)
    extension_flag = models.BooleanField(default=False)
    requested_datetime = models.DateTimeField()
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    what_varied = models.CharField(max_length=4000)
    why_varied = models.CharField(max_length=4000, null=True)
    when_varied = models.DateField(null=True)
    reject_cancellation_reason = models.CharField(max_length=4000, null=True)
    update_request_reason = models.CharField(max_length=4000, null=True)
    closed_datetime = models.DateTimeField(null=True)
    closed_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")


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
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    closed_datetime = models.DateTimeField(null=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="+")
    template_code = models.CharField(max_length=30)
    email_type = models.CharField(max_length=30)
    constabulary_attachments_xml = models.TextField(null=True)


class ConstabularyEmailAttachments(MigrationBase):
    file_target = models.ForeignKey(FileTarget, on_delete=models.CASCADE)
    caseemail = models.ForeignKey(CaseEmail, on_delete=models.CASCADE)


class CaseNote(MigrationBase):
    ima = models.ForeignKey(Process, on_delete=models.CASCADE, to_field="ima_id", null=True)
    export_application = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=20, null=False, default="DRAFT")
    note = models.TextField(null=True)
    create_datetime = models.DateTimeField(null=False)
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


class UpdateRequest(MigrationBase):
    ima = models.ForeignKey(Process, on_delete=models.CASCADE, to_field="ima_id", null=True)
    export_application = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, null=True)
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


class FurtherInformationRequest(MigrationBase):
    ia_ima = models.ForeignKey(Process, on_delete=models.CASCADE, to_field="ima_id", null=True)
    export_application = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, null=True)
    access_request = models.ForeignKey(AccessRequest, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=20)
    request_subject = models.CharField(max_length=100, null=True)
    request_detail = models.TextField(null=True)
    email_cc_address_list_str = models.TextField(null=True)
    requested_datetime = models.DateTimeField(null=True)
    response_detail = models.TextField(null=True)
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
    create_datetime = models.DateTimeField()
    published_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    published_datetime = models.DateTimeField(null=True)
    retracted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    retracted_datetime = models.DateTimeField(null=True)
    reference = models.CharField(max_length=100, null=True)
    version = models.PositiveIntegerField(default=0)
    folder = models.OneToOneField(FileFolder, on_delete=models.CASCADE, related_name="mailshot")


class WithdrawApplication(MigrationBase):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.CASCADE, null=True)
    export_application = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField()
    status = models.CharField(max_length=10)
    reason = models.TextField()
    request_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    response = models.TextField()
    response_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    created_datetime = models.DateTimeField()
    updated_datetime = models.DateTimeField()
