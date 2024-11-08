from django.db import models

from data_migration.models.base import MigrationBase
from data_migration.models.flow import Process
from data_migration.models.reference import Country, CountryGroup
from data_migration.models.user import Exporter, Office, User


class ExportApplicationType(MigrationBase):
    is_active = models.BooleanField(null=False, default=True)
    type_code = models.CharField(max_length=30, null=False, unique=True)
    type = models.CharField(max_length=70, null=False)
    allow_multiple_products = models.BooleanField(null=False)
    generate_cover_letter = models.BooleanField(null=False)
    allow_hse_authorization = models.BooleanField(null=False)
    country_group_legacy = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        null=False,
        related_name="+",
        to_field="country_group_id",
    )
    country_of_manufacture_cg = models.ForeignKey(
        CountryGroup,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
        to_field="country_group_id",
    )


class ExportApplication(MigrationBase):
    ca = models.ForeignKey(Process, on_delete=models.CASCADE, to_field="ca_id")
    cad_id = models.PositiveIntegerField(unique=True)
    status = models.CharField(max_length=30, default="IN_PROGRESS")
    submit_datetime = models.DateTimeField(null=True)
    reference = models.CharField(max_length=100, null=True, unique=True)
    decision = models.CharField(max_length=10, null=True)
    refuse_reason = models.CharField(max_length=4000, null=True)
    application_type = models.ForeignKey(
        ExportApplicationType, on_delete=models.PROTECT, null=False
    )
    last_update_datetime = models.DateTimeField()
    last_updated_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=False, null=False, related_name="updated_export_cases"
    )
    variation_no = models.IntegerField(null=False, default=0)
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    exporter = models.ForeignKey(Exporter, on_delete=models.PROTECT, related_name="+")
    exporter_office_legacy = models.ForeignKey(
        Office, on_delete=models.PROTECT, null=True, related_name="+", to_field="legacy_id"
    )
    contact = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    agent = models.ForeignKey(Exporter, on_delete=models.PROTECT, null=True, related_name="+")
    agent_office_legacy = models.ForeignKey(
        Office, on_delete=models.PROTECT, null=True, related_name="+", to_field="legacy_id"
    )
    case_owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    case_note_xml = models.TextField(null=True)
    fir_xml = models.TextField(null=True)
    update_request_xml = models.TextField(null=True)
    variations_xml = models.TextField(null=True)
    withdrawal_xml = models.TextField(null=True)


class ExportApplicationCountries(MigrationBase):
    cad = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, to_field="cad_id")
    country = models.ForeignKey(Country, on_delete=models.CASCADE)


class ExportApplicationCertificate(MigrationBase):
    ca = models.ForeignKey(
        Process, on_delete=models.PROTECT, related_name="certificates", to_field="ca_id"
    )
    cad_id = models.PositiveIntegerField(unique=True)
    case_completion_datetime = models.DateTimeField(null=True)
    status = models.TextField(max_length=2, default="DR")
    case_reference = models.CharField(max_length=100, null=True, unique=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    document_pack_id = models.IntegerField(unique=True, null=True)
    revoke_reason = models.TextField(null=True)
    revoke_email_sent = models.BooleanField(default=False)


class ExportBase(MigrationBase):
    PROCESS_PK = True

    class Meta:
        abstract = True
