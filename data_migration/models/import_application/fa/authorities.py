from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import F
from django.db.models.expressions import Window
from django.db.models.functions import RowNumber

from data_migration import queries
from data_migration.models.base import MigrationBase
from data_migration.models.file import FileFolder
from data_migration.models.reference import Constabulary
from data_migration.models.user import Importer, Office, User


class FirearmsAuthority(MigrationBase):
    is_active = models.BooleanField(null=False, default=True)
    reference = models.CharField(max_length=100, null=True)
    certificate_type = models.CharField(max_length=20, null=True)
    postcode = models.CharField(max_length=30, null=True)
    address = models.CharField(max_length=300, null=True)
    address_entry_type = models.CharField(max_length=10, null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    further_details = models.CharField(max_length=4000, null=True)
    issuing_constabulary = models.ForeignKey(Constabulary, on_delete=models.PROTECT, null=True)
    importer = models.ForeignKey(Importer, on_delete=models.PROTECT, null=False)
    act_quantity_xml = models.TextField(null=True)
    file_folder = models.ForeignKey(FileFolder, null=True, on_delete=models.SET_NULL)
    archive_reason = models.CharField(max_length=60, null=True)
    other_archive_reason = models.TextField(null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["file_folder_id"]

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)

        archive_reason = data["archive_reason"]

        if archive_reason:
            data["archive_reason"] = archive_reason.split(",")

        return data


class FirearmsAct(MigrationBase):
    act = models.CharField(max_length=100)
    description = models.TextField(null=True)
    is_active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by_id = models.IntegerField()
    updated_datetime = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+", null=True)


class ActQuantity(MigrationBase):
    firearmsauthority = models.ForeignKey(FirearmsAuthority, on_delete=models.PROTECT)
    firearmsact = models.ForeignKey(FirearmsAct, on_delete=models.PROTECT)
    quantity = models.IntegerField(null=True)
    infinity = models.BooleanField(default=False)


class FirearmsAuthorityOffice(MigrationBase):
    firearmsauthority = models.ForeignKey(FirearmsAuthority, on_delete=models.CASCADE)
    office_legacy = models.ForeignKey(Office, on_delete=models.CASCADE, to_field="legacy_id")

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["office_legacy_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return super().get_values_kwargs() | {"office_id": F("office_legacy__id")}


class FirearmsAuthorityFile(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = data.pop("row_number")
        return data

    @classmethod
    def get_source_data(cls) -> Generator:
        return (
            FirearmsAuthority.objects.select_related("file_folder")
            .prefetch_related("file_folder__file_targets__files")
            .annotate(row_number=Window(expression=RowNumber()))
            .exclude(file_folder__file_targets__files__id__isnull=True)
            .values(
                "row_number",
                file_id=F("file_folder__file_targets__files__id"),
                firearmsauthority_id=F("id"),
            )
            .iterator(chunk_size=2000)
        )


class Section5Authority(MigrationBase):
    is_active = models.BooleanField(null=False, default=True)
    reference = models.CharField(max_length=100, null=True)
    postcode = models.CharField(max_length=30, null=True)
    address = models.CharField(max_length=300, null=True)
    address_entry_type = models.CharField(max_length=10, null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    further_details = models.CharField(max_length=4000, null=True)
    importer = models.ForeignKey(Importer, on_delete=models.PROTECT, null=False)
    clause_quantity_xml = models.TextField(null=True)
    file_folder = models.ForeignKey(FileFolder, null=True, on_delete=models.SET_NULL)
    archive_reason = models.CharField(max_length=60, null=True)
    other_archive_reason = models.TextField(null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["file_folder_id"]

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = super().data_export(data)

        archive_reason = data["archive_reason"]

        if archive_reason:
            data["archive_reason"] = archive_reason.split(",")

        return data


class Section5Clause(MigrationBase):
    UPDATE_TIMESTAMP_QUERY = queries.section5_clause_timestamp_update

    clause = models.CharField(max_length=100)
    legacy_code = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")
    updated_datetime = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+", null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["legacy_code"]


class ClauseQuantity(MigrationBase):
    section5authority = models.ForeignKey(Section5Authority, on_delete=models.PROTECT)
    section5clause = models.ForeignKey(Section5Clause, on_delete=models.PROTECT)
    quantity = models.IntegerField(null=True)
    infinity = models.BooleanField(default=False)


class Section5AuthorityOffice(MigrationBase):
    section5authority = models.ForeignKey(Section5Authority, on_delete=models.CASCADE)
    office_legacy = models.ForeignKey(Office, on_delete=models.CASCADE, to_field="legacy_id")

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["office_legacy_id"]

    @classmethod
    def get_values_kwargs(cls) -> dict[str, Any]:
        return super().get_values_kwargs() | {"office_id": F("office_legacy__id")}


class Section5AuthorityFile(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = data.pop("row_number")
        return data

    @classmethod
    def get_source_data(cls) -> Generator:
        return (
            Section5Authority.objects.select_related("file_folder")
            .prefetch_related("file_folder__file_targets__files")
            .annotate(row_number=Window(expression=RowNumber()))
            .exclude(file_folder__file_targets__files__id__isnull=True)
            .values(
                "row_number",
                file_id=F("file_folder__file_targets__files__id"),
                section5authority_id=F("id"),
            )
            .iterator(chunk_size=2000)
        )
