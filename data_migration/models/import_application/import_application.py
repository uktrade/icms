from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.file import FileFolder
from data_migration.models.flow import Process
from data_migration.models.reference import CommodityGroup, Country, UniqueReference
from data_migration.models.user import Importer, Office, User

from .import_application_type import ImportApplicationType


class ImportApplication(MigrationBase):
    PROCESS_PK = True

    file_folder = models.OneToOneField(
        FileFolder, on_delete=models.PROTECT, related_name="import_application", null=True
    )
    ima = models.OneToOneField(Process, on_delete=models.PROTECT, to_field="ima_id")
    imad_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=30)
    submit_datetime = models.DateTimeField(null=True)
    reference = models.CharField(max_length=100, null=True, unique=True)
    decision = models.CharField(max_length=10, null=True)

    refuse_reason = models.CharField(
        max_length=4000,
        null=True,
    )

    applicant_reference = models.CharField(max_length=500, null=True)
    create_datetime = models.DateTimeField(null=False)
    variation_no = models.IntegerField(null=False, default=0)
    legacy_case_flag = models.CharField(max_length=5, null=True)
    chief_usage_status = models.CharField(max_length=1, null=True)
    variation_decision = models.CharField(max_length=10, null=True)
    variation_refuse_reason = models.CharField(max_length=4000, null=True)
    licence_extended_flag = models.CharField(max_length=5, null=True)
    last_update_datetime = models.DateTimeField(null=True)
    application_type = models.ForeignKey(
        ImportApplicationType, on_delete=models.PROTECT, null=False
    )

    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    last_updated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    importer = models.ForeignKey(Importer, on_delete=models.PROTECT, null=True, related_name="+")
    agent = models.ForeignKey(Importer, on_delete=models.PROTECT, null=True, related_name="+")
    importer_office_legacy = models.ForeignKey(
        Office, on_delete=models.PROTECT, null=True, related_name="+", to_field="legacy_id"
    )
    agent_office_legacy = models.ForeignKey(
        Office, on_delete=models.PROTECT, null=True, related_name="+", to_field="legacy_id"
    )
    contact = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")

    origin_country = models.ForeignKey(
        Country, on_delete=models.PROTECT, null=True, related_name="+"
    )

    consignment_country = models.ForeignKey(
        Country, on_delete=models.PROTECT, null=True, related_name="+"
    )

    commodity_group = models.ForeignKey(CommodityGroup, on_delete=models.PROTECT, null=True)
    case_owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    cover_letter_text = models.TextField(null=True)

    imi_submitted_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, related_name="+"
    )

    imi_submit_datetime = models.DateTimeField(null=True)
    variations_xml = models.TextField(null=True)
    withdrawal_xml = models.TextField(null=True)
    licence_uref = models.ForeignKey(
        UniqueReference, on_delete=models.PROTECT, null=True, to_field="uref"
    )


class ChecklistBase(MigrationBase):
    class Meta:
        abstract = True

    case_update = models.CharField(max_length=3, null=True)
    fir_required = models.CharField(max_length=3, null=True)
    response_preparation = models.CharField(max_length=5, null=True)
    validity_period_correct = models.CharField(max_length=3, null=True)
    endorsements_listed = models.CharField(max_length=3, null=True)
    authorisation = models.CharField(max_length=5, null=True)


class ImportApplicationLicence(MigrationBase):
    ima = models.ForeignKey(
        Process, on_delete=models.PROTECT, related_name="licences", to_field="ima_id"
    )
    # Each variation has a different imad_id so can use it to link documents to the same variation
    imad_id = models.PositiveIntegerField(unique=True)
    status = models.TextField(max_length=2, default="DR")
    issue_paper_licence_only = models.BooleanField(null=True)
    licence_start_date = models.DateField(null=True)
    licence_end_date = models.DateField(null=True)
    case_completion_datetime = models.DateTimeField(null=True)
    case_reference = models.CharField(max_length=100, null=True, unique=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    issue_datetime = models.DateTimeField(null=True)  # For data comparisons only
    document_pack_id = models.IntegerField(unique=True, null=True)
    revoke_reason = models.TextField(null=True)
    revoke_email_sent = models.BooleanField()


class EndorsementImportApplication(MigrationBase):
    imad = models.ForeignKey(ImportApplication, on_delete=models.PROTECT, to_field="imad_id")
    content = models.TextField()
    created_datetime = models.DateTimeField(null=True)
    updated_datetime = models.DateTimeField(auto_now=True)


class SIGLTransmission(MigrationBase):
    ima = models.ForeignKey(Process, on_delete=models.CASCADE, to_field="ima_id")
    status = models.CharField(max_length=8)
    transmission_type = models.CharField(max_length=12)
    request_type = models.CharField(max_length=8)
    sent_datetime = models.DateTimeField()
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
    response_datetime = models.DateTimeField(null=True)
    response_message = models.CharField(max_length=120, null=True)
    response_code = models.IntegerField(null=True)


class ImportApplicationBase(MigrationBase):
    class Meta:
        abstract = True
