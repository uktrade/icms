import os.path
from typing import Any, Dict

from django import forms
from django.db import models
from django_chunk_upload_handlers.clam_av import validate_virus_check_result
from storages.backends.s3boto3 import S3Boto3StorageFile

from web.domains.user.models import User
from web.utils.s3 import delete_file_from_s3

EXTENSION_BLACKLIST = [
    "bat",
    "bin",
    "com",
    "dll",
    "exe",
    "htm",
    "html",
    "msc",
    "msi",
    "msp",
    "ocx",
    "scr",
    "wsc",
    "wsf",
    "wsh",
]


class ICMSFileField(forms.FileField):
    def __init__(self, *, validators=(), **kwargs) -> None:
        super().__init__(
            # order is important: validate_file_extension can delete the file
            # from S3, so has to be after the virus check
            validators=[validate_virus_check_result, validate_file_extension, *validators],
            **kwargs,
        )


def validate_file_extension(file: S3Boto3StorageFile) -> None:
    """Django validator that blocks forbidden file extensions in ICMS."""

    file_name, file_extension = os.path.splitext(file.name)

    if file_extension.lstrip(".") in EXTENSION_BLACKLIST:
        # by the time custom validations are called, file upload handlers have
        # already done their job and the file is in S3, so we have to delete it
        delete_file_from_s3(file.name)

        raise forms.ValidationError(
            "Invalid file extension. These extensions are not allowed: "
            + ", ".join(EXTENSION_BLACKLIST)
        )


# TODO: related_file_manager is something like
# models.manager.RelatedManager[File], but that's a class Django dynamically
# creates at runtime, you can't even import it
def create_file_model(
    f: S3Boto3StorageFile,
    created_by: User,
    related_file_manager: Any,
    extra_args: Dict[str, Any] = None,
) -> models.Model:
    """Create File (or sub-class) model, add it to the related set. Note that
    the create call here is
    https://docs.djangoproject.com/en/3.2/ref/models/relations/#django.db.models.fields.related.RelatedManager.create,
    not the standard Django model create."""

    if extra_args is None:
        extra_args = {}

    return related_file_manager.create(
        filename=f.original_name,
        file_size=f.file_size,
        content_type=f.content_type,
        path=f.name,
        created_by=created_by,
        **extra_args,
    )
