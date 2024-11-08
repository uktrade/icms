from django.db import models

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


class FileM2MBase(MigrationBase):
    class Meta:
        abstract = True
