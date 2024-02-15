from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import F

from data_migration.models.base import MigrationBase
from data_migration.models.file import FileFolder
from data_migration.models.flow import Process
from data_migration.models.reference import CommodityGroup, Country
from data_migration.models.user import Importer, Office, User
from data_migration.utils.format import (
    reformat_placeholders,
    str_to_bool,
    str_to_yes_no,
    strip_foxid_attribute,
)

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
    last_update_datetime = models.DateTimeField(null=False, auto_now=True)
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

    @classmethod
    def get_excludes(cls) -> list[str]:
        return [
            "ima_id",
            "imad_id",
            "file_folder_id",
            "importer_office_legacy_id",
            "agent_office_legacy_id",
            "variations_xml",
            "withdrawal_xml",
        ]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {
            "importer_office_id": F("importer_office_legacy__id"),
            "agent_office_id": F("agent_office_legacy__id"),
            "process_ptr_id": F("id"),
            "last_submit_datetime": F("submit_datetime"),
        }

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        for field in data.keys():
            if field.endswith("_flag"):
                value = data[field]
                data[field] = bool(value) and value.lower() == "true"

        # TODO ICMSLST-1694: Nullify for now
        data["licence_reference"] = None

        cover_letter_text = data["cover_letter_text"]

        variation_no = data["variation_no"]

        if variation_no > 0:
            reference = data["reference"]
            data["reference"] = f"{reference}/{variation_no}"

        if cover_letter_text:
            cover_letter_text = strip_foxid_attribute(cover_letter_text)
            cover_letter_text = reformat_placeholders(cover_letter_text)

        data["cover_letter_text"] = cover_letter_text

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
    def y_n_fields(cls) -> list[str]:
        """Return a list of fields to be parsed to yes, no or n/a"""
        return ["case_update", "fir_required", "validity_period_correct", "endorsements_listed"]

    @classmethod
    def bool_fields(cls) -> list[str]:
        """Return a list of fields to be parsed to bool"""
        return ["response_preparation", "authorisation"]

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["import_application_id"] = data.pop("imad__id")

        for field in data.keys():
            if field in cls.bool_fields():
                data[field] = str_to_bool(data[field]) or False
            elif field in cls.y_n_fields():
                data[field] = str_to_yes_no(data[field])
        return data

    @classmethod
    def get_source_data(cls) -> Generator:
        """Queries the model to get the queryset of data for the V2 import"""

        values = cls.get_values()
        values_kwargs = cls.get_values_kwargs()
        related = cls.get_related()
        cl_excludes = {f"{f}__isnull": True for f in values if not f.endswith("id")}

        return (
            cls.objects.select_related(*related)
            .exclude(**cl_excludes)
            .values(*values, **values_kwargs)
            .iterator(chunk_size=2000)
        )

    @classmethod
    def get_includes(cls) -> list[str]:
        return ["imad__id"]

    @classmethod
    def get_excludes(cls) -> list[str]:
        return ["imad_id"]


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
    document_pack_id = models.IntegerField(unique=True, null=True)

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["import_application_id"] = data.pop("ima__id")

        return data

    @classmethod
    def get_includes(cls) -> list[str]:
        return ["ima__id"]

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["ima_id", "imad_id", "document_pack_id"]


class EndorsementImportApplication(MigrationBase):
    imad = models.ForeignKey(ImportApplication, on_delete=models.PROTECT, to_field="imad_id")
    content = models.TextField()
    created_datetime = models.DateTimeField(null=True)
    updated_datetime = models.DateTimeField(auto_now=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["imad_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return {"import_application_id": F("imad__id")}


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

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["ima_id"]

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        return cls.objects.values(
            "id", sigltransmission_id=F("id"), importapplication_id=F("ima__id")
        ).iterator(chunk_size=2000)


class ImportApplicationBase(MigrationBase):
    PROCESS_PK = True

    class Meta:
        abstract = True

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["importapplication_ptr_id"] = data.pop("imad__id")

        return data

    @classmethod
    def get_includes(cls) -> list[str]:
        return super().get_includes() + ["imad__id"]

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["imad_id"]

    @classmethod
    def models_to_populate(cls) -> list[str]:
        return ["Process", "ImportApplication", cls.__name__]
