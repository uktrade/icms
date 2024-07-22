from collections.abc import Generator
from typing import Any

from django.db import models
from django.db.models import F
from django.db.models.expressions import Window
from django.db.models.functions import RowNumber

from .base import MigrationBase
from .user import User


class FileFolder(MigrationBase):
    """Model for V1 table DECMGR.FILE_FOLDERS; parent of DECMGR.FILE_TARGETS"""

    app_model = models.CharField(max_length=40, null=True)
    folder_id = models.AutoField(auto_created=True, primary_key=True)
    folder_type = models.CharField(max_length=30)


class FileTarget(MigrationBase):
    """Model for V1 table DECMGR.FILE_TARGETS; parent of DECMGR.FILE_VERSIONS"""

    target_id = models.AutoField(auto_created=True, primary_key=True)
    folder = models.ForeignKey(
        FileFolder, on_delete=models.CASCADE, related_name="file_targets", null=True
    )
    target_type = models.CharField(max_length=30)
    status = models.CharField(max_length=20, null=True)


class DocFolder(MigrationBase):
    """This model is for DOCLIBMGR.FOLDERS folders"""

    doc_folder_id = models.AutoField(auto_created=True, primary_key=True)
    folder_title = models.CharField(max_length=30)


class File(MigrationBase):
    version_id = models.IntegerField(null=True)
    is_active = models.BooleanField(default=True)
    filename = models.CharField(max_length=300)
    content_type = models.CharField(max_length=100, null=True)
    file_size = models.IntegerField()
    path = models.CharField(max_length=4000)
    created_datetime = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    created_by_str = models.CharField(max_length=255, null=True)
    target = models.ForeignKey(
        FileTarget, on_delete=models.CASCADE, related_name="files", null=True
    )
    doc_folder = models.ForeignKey(
        DocFolder, on_delete=models.CASCADE, related_name="files", null=True
    )
    document_legacy_id = models.IntegerField(unique=True, null=True)

    # firearms supplementary report file id
    sr_goods_file_id = models.CharField(max_length=20, null=True, unique=True)

    report_output_id = models.IntegerField(null=True, unique=True)

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        # Data fix for pdf files without content_type set, fixing so the metadata can be migrated
        # and maintain the reference to the S3 object
        # Note that these files in V1 have a file_size of 0 bytes and are not able to be opened

        if not data["content_type"]:
            if data["filename"].endswith(".pdf"):
                data["content_type"] = "application/pdf"
            if data["filename"].endswith(".docx"):
                docx = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                data["content_type"] = docx

        return data

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + [
            "version_id",
            "target_id",
            "doc_folder_id",
            "document_legacy_id",
            "created_by_str",
            "sr_goods_file_id",
            "report_output_id",
        ]


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
    def get_m2m_filter_kwargs(cls) -> dict[str, Any]:
        filter_kwargs: dict[str, str | list[str]] = {
            "target__folder__folder_type": cls.FOLDER_TYPE,
        }

        if isinstance(cls.TARGET_TYPE, list):
            filter_kwargs["target__target_type__in"] = cls.TARGET_TYPE
        else:
            filter_kwargs["target__target_type"] = cls.TARGET_TYPE

        if cls.FILTER_APP_MODEL:
            filter_kwargs["target__folder__app_model"] = cls.APP_MODEL

        return filter_kwargs

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        if not cls.APP_MODEL:
            raise NotImplementedError("APP_MODEL must be defined on the model")

        filter_kwargs = cls.get_m2m_filter_kwargs()

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
