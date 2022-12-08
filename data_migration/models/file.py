from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import F, Q, QuerySet
from django.db.models.expressions import Window
from django.db.models.functions import RowNumber

from .base import MigrationBase
from .user import User


class FileCombined(MigrationBase):
    app_model = models.CharField(max_length=40, null=True)
    doc_folder_id = models.IntegerField(null=True)
    folder_id = models.IntegerField(null=True)
    folder_type = models.CharField(max_length=30)
    folder_title = models.CharField(max_length=30, null=True)
    target_id = models.IntegerField(null=True)
    target_type = models.CharField(max_length=30, null=True)
    status = models.CharField(max_length=20, null=True)
    version_id = models.IntegerField(null=True)
    file_id = models.IntegerField(null=True)
    filename = models.CharField(max_length=300, null=True)
    content_type = models.CharField(max_length=100, null=True)
    file_size = models.IntegerField(null=True)
    path = models.CharField(max_length=4000, null=True)
    created_datetime = models.DateTimeField(null=True)
    created_by_id = models.IntegerField(null=True)


class FileFolder(MigrationBase):
    """This model is for DECMGR.FILE_FOLDERS"""

    app_model = models.CharField(max_length=40, null=True)
    folder_id = models.AutoField(auto_created=True, primary_key=True)
    folder_type = models.CharField(max_length=30)

    @classmethod
    def get_from_combined(cls) -> QuerySet:
        return (
            FileCombined.objects.exclude(folder_id__isnull=True)
            .values("app_model", "folder_type", "folder_id")
            .distinct()
            .iterator(chunk_size=2000)
        )


class FileTarget(MigrationBase):
    """This model is for DECMGR.FILE_TARGETS"""

    target_id = models.AutoField(auto_created=True, primary_key=True)
    folder = models.ForeignKey(
        FileFolder, on_delete=models.CASCADE, related_name="file_targets", null=True
    )
    target_type = models.CharField(max_length=30)
    status = models.CharField(max_length=20, null=True)

    @classmethod
    def get_from_combined(cls) -> QuerySet:
        return (
            FileCombined.objects.filter(target_id__isnull=False)
            .values("folder_id", "target_type", "status", "target_id")
            .distinct()
            .iterator(chunk_size=2000)
        )


class DocFolder(MigrationBase):
    """This model is for DOCLIBMGR.FOLDERS folders"""

    doc_folder_id = models.AutoField(auto_created=True, primary_key=True)
    folder_title = models.CharField(max_length=30)

    @classmethod
    def get_from_combined(cls) -> QuerySet:
        return (
            FileCombined.objects.exclude(doc_folder_id__isnull=True)
            .values("folder_title", "doc_folder_id")
            .distinct()
            .iterator(chunk_size=2000)
        )


class File(MigrationBase):
    # TODO: created_by_str can be an email or id. Need to process and fix data
    is_active = models.BooleanField(default=True)
    filename = models.CharField(max_length=300)
    content_type = models.CharField(max_length=100)
    file_size = models.IntegerField()
    path = models.CharField(max_length=4000)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    created_by_str = models.CharField(max_length=255, null=True)
    target = models.ForeignKey(
        FileTarget, on_delete=models.CASCADE, related_name="files", null=True
    )
    doc_folder = models.ForeignKey(
        DocFolder, on_delete=models.CASCADE, related_name="files", null=True
    )
    document_legacy_id = models.IntegerField(unique=True, null=True)

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + [
            "target_id",
            "doc_folder_id",
            "document_legacy_id",
            "created_by_str",
        ]

    @classmethod
    def get_from_combined(cls) -> QuerySet:
        return (
            FileCombined.objects.exclude(content_type__isnull=True)
            .filter(Q(file_id__isnull=False) | (Q(version_id__isnull=False) & Q(status="RECEIVED")))
            .values(
                "filename",
                "content_type",
                "file_size",
                "path",
                "created_datetime",
                "created_by_id",
                "target_id",
                "doc_folder_id",
            )
            .iterator(chunk_size=2000)
        )


class FileM2MBase(MigrationBase):
    TARGET_TYPE: str | list[str] = "IMP_SUPPORTING_DOC"
    FOLDER_TYPE: str = "IMP_APP_DOCUMENTS"
    FILE_MODEL: str = "file"
    APP_MODEL: str = ""
    FILTER_APP_MODEL = True

    class Meta:
        abstract = True

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = data.pop("row_number")
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        if not cls.APP_MODEL:
            raise NotImplementedError("APP_MODEL must be defined on the model")

        filter_kwargs: dict[str, str | list[str]] = {
            "target__folder__folder_type": cls.FOLDER_TYPE,
        }

        if isinstance(cls.TARGET_TYPE, list):
            filter_kwargs["target__target_type__in"] = cls.TARGET_TYPE
        else:
            filter_kwargs["target__target_type"] = cls.TARGET_TYPE

        if cls.FILTER_APP_MODEL:
            filter_kwargs["target__folder__app_model"] = cls.APP_MODEL

        return (
            File.objects.select_related("target__folder__import_application")
            .filter(**filter_kwargs)
            .annotate(row_number=Window(expression=RowNumber()))
            .values(
                "row_number",
                **{
                    f"{cls.FILE_MODEL}_id": F("pk"),
                    f"{cls.APP_MODEL}_id": F("target__folder__import_application__pk"),
                },
            )
            .iterator(chunk_size=2000)
        )
