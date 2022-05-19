from typing import TYPE_CHECKING

from django.db import models

from .base import MigrationBase
from .user import User

if TYPE_CHECKING:
    from django.db.models import QuerySet


class FileCombined(MigrationBase):
    folder_id = models.IntegerField()
    folder_type = models.CharField(max_length=30)
    target_id = models.IntegerField(null=True)
    target_type = models.CharField(max_length=30, null=True)
    status = models.CharField(max_length=20, null=True)
    version_id = models.IntegerField(null=True)
    filename = models.CharField(max_length=300, null=True)
    content_type = models.CharField(max_length=100, null=True)
    file_size = models.IntegerField(null=True)
    path = models.CharField(max_length=4000, null=True)
    created_datetime = models.DateTimeField(null=True)
    created_by_id = models.IntegerField(null=True)


class FileFolder(MigrationBase):
    folder_id = models.AutoField(auto_created=True, primary_key=True)
    folder_type = models.CharField(max_length=30)

    @classmethod
    def get_from_combined(cls) -> "QuerySet":
        return FileCombined.objects.values("folder_type", "folder_id").distinct()


class FileTarget(MigrationBase):
    target_id = models.AutoField(auto_created=True, primary_key=True)
    folder = models.ForeignKey(
        FileFolder, on_delete=models.CASCADE, related_name="file_targets", null=True
    )
    target_type = models.CharField(max_length=30)
    status = models.CharField(max_length=20, null=True)

    @classmethod
    def get_from_combined(cls) -> "QuerySet":
        return (
            FileCombined.objects.filter(target_id__isnull=False)
            .values("folder_id", "target_type", "status", "target_id")
            .distinct()
        )


class File(MigrationBase):
    is_active = models.BooleanField(default=True)
    filename = models.CharField(max_length=300)
    content_type = models.CharField(max_length=100)
    file_size = models.IntegerField()
    path = models.CharField(max_length=4000)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    target = models.ForeignKey(
        FileTarget, on_delete=models.CASCADE, related_name="files", null=True
    )

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["target_id"]

    @classmethod
    def get_from_combined(cls) -> "QuerySet":
        return FileCombined.objects.filter(version_id__isnull=False).values(
            "filename",
            "content_type",
            "file_size",
            "path",
            "created_datetime",
            "created_by_id",
            "target_id",
        )
