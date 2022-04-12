from django.db import models

from .base import MigrationBase
from .user import User


class FileTarget(MigrationBase):
    folder_type = models.CharField(max_length=30, null=True)
    target_type = models.CharField(max_length=30, null=True)
    status = models.CharField(max_length=20, null=True)


class File(MigrationBase):
    is_active = models.BooleanField(default=True)
    filename = models.CharField(max_length=300)
    content_type = models.CharField(max_length=100)
    file_size = models.IntegerField()
    path = models.CharField(max_length=4000)
    created_datetime = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    target = models.ForeignKey(
        FileTarget, on_delete=models.SET_NULL, null=True, related_name="files"
    )

    @classmethod
    def get_excludes(cls) -> list[str]:
        return super().get_excludes() + ["target_id"]
