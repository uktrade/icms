from typing import Any

from django.db import models
from django.db.models import F

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

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["country_group_legacy_id", "country_of_manufacture_cg_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {
            "country_group_id": F("country_group_legacy__id"),
            "country_group_for_manufacture_id": F("country_of_manufacture_cg__id"),
        }


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
    last_update_datetime = models.DateTimeField(null=False, auto_now=True)
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
    contact = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )
    agent = models.ForeignKey(Exporter, on_delete=models.PROTECT, null=True, related_name="+")
    agent_office_legacy = models.ForeignKey(
        Office, on_delete=models.PROTECT, null=True, related_name="+", to_field="legacy_id"
    )
    case_owner = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    case_note_xml = models.TextField(null=True)
    fir_xml = models.TextField(null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + [
            "ca_id",
            "cad_id",
            "exporter_office_legacy_id",
            "agent_office_legacy_id",
        ]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {
            "process_ptr_id": F("id"),
            "exporter_office_id": F("exporter_office_legacy__id"),
            "agent_office_id": F("agent_office_legacy__id"),
        }

    # TODO update_requests = models.ManyToManyField(UpdateRequest)


class ExportApplicationCountries(MigrationBase):
    cad = models.ForeignKey(ExportApplication, on_delete=models.CASCADE, to_field="cad_id")
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["cad_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"exportapplication_id": F("cad__id")}


class ExportApplicationCertificate(MigrationBase):
    ca = models.ForeignKey(
        Process, on_delete=models.PROTECT, related_name="certificates", to_field="ca_id"
    )
    cad_id = models.PositiveIntegerField(unique=True)
    case_completion_datetime = models.DateTimeField(null=True)
    status = models.TextField(max_length=2, default="DR")
    case_reference = models.CharField(max_length=100, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["ca_id", "cad_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"export_application_id": F("ca__id")}


class ExportBase(MigrationBase):
    PROCESS_PK = True

    class Meta:
        abstract = True

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", "ExportApplication", cls.__name__]

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["cad_id", "file_folder_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"exportapplication_ptr_id": F("id")}
