from typing import Any, Generator

from django.db import models
from django.db.models import F
from django.db.models.expressions import Window
from django.db.models.functions import RowNumber

from .base import MigrationBase
from .file import File, FileFolder
from .import_application import ImportApplication
from .user import User


class CaseReference(MigrationBase):
    prefix = models.CharField(max_length=8)
    year = models.IntegerField(null=True)
    reference = models.IntegerField()


class VariationRequest(MigrationBase):
    import_application = models.ForeignKey(ImportApplication, on_delete=models.SET_NULL, null=True)
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
        return super().get_excludes() + ["import_application_id"]

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        return (
            cls.objects.select_related("import_application")
            .values(
                "id", importapplication_id=F("import_application__id"), variationrequest_id=F("id")
            )
            .iterator()
        )


class CaseEmail(MigrationBase):
    imad = models.ForeignKey(
        ImportApplication, on_delete=models.SET_NULL, to_field="imad_id", null=True
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
        return super().get_excludes() + ["imad_id"]

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        address_list_str = data.pop("cc_address_list_str") or ""
        data["cc_address_list"] = address_list_str.split(";")

        return data

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        return (
            cls.objects.select_related("imad")
            .values("id", importapplication_id=F("imad__id"), caseemail_id=F("id"))
            .iterator()
        )


class CaseNote(MigrationBase):
    imad = models.ForeignKey(
        ImportApplication, on_delete=models.SET_NULL, to_field="imad_id", null=True
    )
    is_active = models.BooleanField(null=False, default=True)
    status = models.CharField(max_length=20, null=False, default="DRAFT")
    note = models.TextField(null=True)
    create_datetime = models.DateTimeField(null=False, auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=False)
    file_folder = models.OneToOneField(
        FileFolder,
        on_delete=models.CASCADE,
        related_name="case_note",
    )

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["imad_id", "file_folder_id"]

    @classmethod
    def data_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        return (
            cls.objects.select_related("imad")
            .values("id", importapplication_id=F("imad__id"), casenote_id=F("id"))
            .iterator()
        )


class CaseNoteFile(MigrationBase):
    class Meta:
        abstract = True

    @classmethod
    def m2m_export(cls, data: dict[str, Any]) -> dict[str, Any]:
        data["id"] = data.pop("row_number")
        return data

    @classmethod
    def get_m2m_data(cls, target: models.Model) -> Generator:
        return (
            File.objects.select_related("target__folder__case_note_id")
            .filter(
                target__folder__folder_type="IMP_CASE_NOTE_DOCUMENTS",
                target__folder__case_note__isnull=False,
            )
            .annotate(row_number=Window(expression=RowNumber()))
            .values(
                "row_number",
                file_id=F("pk"),
                casenote_id=F("target__folder__case_note__pk"),
            )
            .iterator()
        )
