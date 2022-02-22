from typing import Any

from django.db import models

from data_migration.models.base import MigrationBase, Process
from data_migration.models.reference import CommodityGroup, Country
from data_migration.models.user import Importer, Office, User

from .import_application_type import ImportApplicationType


class ImportApplication(MigrationBase):
    ima = models.OneToOneField(Process, on_delete=models.PROTECT, to_field="ima_id")
    imad_id = models.IntegerField(unique=True)
    status = models.CharField(max_length=30)
    submit_datetime = models.DateTimeField(blank=True, null=True)
    reference = models.CharField(max_length=100, blank=True, null=True, unique=True)
    decision = models.CharField(max_length=10, blank=True, null=True)

    refuse_reason = models.CharField(
        max_length=4000,
        blank=True,
        null=True,
    )

    # TODO: Find acknowledged fields in source or remove from model
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )

    acknowledged_datetime = models.DateTimeField(null=True)
    applicant_reference = models.CharField(max_length=500, blank=True, null=True)
    create_datetime = models.DateTimeField(blank=False, null=False)
    variation_no = models.IntegerField(blank=False, null=False, default=0)
    legacy_case_flag = models.CharField(max_length=5, null=True)
    chief_usage_status = models.CharField(max_length=1, null=True)
    under_appeal_flag = models.CharField(max_length=5, null=True)
    variation_decision = models.CharField(max_length=10, null=True)
    variation_refuse_reason = models.CharField(max_length=4000, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    licence_start_date = models.DateField(blank=True, null=True)
    licence_end_date = models.DateField(blank=True, null=True)
    licence_extended_flag = models.CharField(max_length=5, null=True)
    licence_reference = models.CharField(max_length=100, null=True, unique=True)
    last_update_datetime = models.DateTimeField(blank=False, null=False, auto_now=True)
    application_type = models.ForeignKey(
        ImportApplicationType, on_delete=models.PROTECT, blank=False, null=False
    )

    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    last_updated_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")
    importer = models.ForeignKey(Importer, on_delete=models.PROTECT, null=True, related_name="+")
    agent = models.ForeignKey(Importer, on_delete=models.PROTECT, null=True, related_name="+")
    importer_office = models.ForeignKey(
        Office, on_delete=models.PROTECT, null=True, related_name="+"
    )
    agent_office = models.ForeignKey(Office, on_delete=models.PROTECT, null=True, related_name="+")
    contact = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name="+")

    origin_country = models.ForeignKey(
        Country, on_delete=models.PROTECT, null=True, related_name="+"
    )

    consignment_country = models.ForeignKey(
        Country, on_delete=models.PROTECT, null=True, related_name="+"
    )

    commodity_group = models.ForeignKey(CommodityGroup, on_delete=models.PROTECT, null=True)
    case_owner = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )
    cover_letter = models.TextField(blank=True, null=True)

    issue_paper_licence_only = models.BooleanField(blank=False, null=True)

    imi_submitted_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, related_name="+"
    )

    imi_submit_datetime = models.DateTimeField(null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return ["ima_id", "imad_id"]

    @classmethod
    def get_includes(cls) -> list[str]:
        return ["ima__id"]

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["process_ptr_id"] = data.pop("ima__id")

        for field in data.keys():
            if field.endswith("_flag"):
                value = data[field]
                data[field] = bool(value) and value.lower() == "true"

        return data


class ChecklistBase(MigrationBase):
    class Meta:
        abstract = True

    case_update = models.CharField(max_length=3, null=True)
    fir_required = models.CharField(max_length=3, null=True)
    response_preparation = models.CharField(max_length=5, null=True)
    validity_period_correct = models.CharField(max_length=3, null=True)
    endorsements_listed = models.CharField(max_length=3, null=True)
    authorisation = models.CharField(max_length=5, null=True)

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["import_application_id"] = data.pop("import_application__id")

        for field in data.keys():
            if field in ["response_preparation", "authorisation"]:
                value = data[field]
                data[field] = bool(value) and value.lower() == "true"
        return data

    @classmethod
    def get_includes(cls) -> list[str]:
        return ["import_application__id"]

    @classmethod
    def get_excludes(cls) -> list[str]:
        return ["imad_id"]


class ImportApplicationBase(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["importapplication_ptr_id"] = data.pop("imad__id")

        return data

    @classmethod
    def get_includes(cls) -> list[str]:
        return ["imad__id"]

    @classmethod
    def get_excludes(cls) -> list[str]:
        return ["imad_id"]
