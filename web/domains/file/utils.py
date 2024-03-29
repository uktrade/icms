import os.path
from typing import Any

from django import forms
from django.db import models
from django_chunk_upload_handlers.clam_av import validate_virus_check_result
from storages.backends.s3boto3 import S3Boto3StorageFile

from web.models import User
from web.utils.s3 import delete_file_from_s3

FILE_EXTENSION_ALLOW_LIST = [
    "bmp",
    "csv",
    "doc",
    "docx",
    "dotx",
    "eml",
    "gif",
    "heic",
    "jfif",
    "jpeg",
    "jpg",
    "msg",
    "odt",
    "pdf",
    "png",
    "rtf",
    "tif",
    "tiff",
    "txt",
    "xls",
    "xlsb",
    "xlsx",
    "xps",
]


HELP_TEXT = "Only the following file extensions (types) are allowed to be uploaded: " + ", ".join(
    FILE_EXTENSION_ALLOW_LIST
)

IMAGE_EXTENSION_ALLOW_LIST = ["jpeg", "jpg", "png"]

IMAGE_HELP_TEXT = (
    "Only the following file extensions (types) are allowed to be uploaded: "
    + ", ".join(IMAGE_EXTENSION_ALLOW_LIST)
)


class ICMSFileField(forms.FileField):
    def __init__(self, *, validators=(), help_text=HELP_TEXT, **kwargs) -> None:
        super().__init__(
            # order is important: validate_file_extension can delete the file
            # from S3, so has to be after the virus check
            validators=[validate_virus_check_result, validate_file_extension, *validators],
            help_text=help_text,
            **kwargs,
        )


class ImageFileField(forms.FileField):
    def __init__(self, *, validators=(), help_text=IMAGE_HELP_TEXT, **kwargs) -> None:
        super().__init__(
            # order is important: validate_file_extension can delete the file
            # from S3, so has to be after the virus check
            validators=[validate_virus_check_result, validate_image_file_extension, *validators],
            help_text=help_text,
            **kwargs,
        )


def validate_file_extension(file: S3Boto3StorageFile) -> None:
    """Django validator that blocks forbidden file extensions in ICMS."""

    _, file_extension = os.path.splitext(file.name)

    if file_extension.lstrip(".").lower() not in FILE_EXTENSION_ALLOW_LIST:
        # by the time custom validations are called, file upload handlers have
        # already done their job and the file is in S3, so we have to delete it
        delete_file_from_s3(file.name)

        raise forms.ValidationError(
            "Invalid file extension. Only these extensions are allowed: "
            + ", ".join(FILE_EXTENSION_ALLOW_LIST)
        )


def validate_image_file_extension(file: S3Boto3StorageFile) -> None:
    """Django validator that only allows specific image file extensions."""

    _, file_extension = os.path.splitext(file.name)

    if file_extension.lstrip(".").lower() not in IMAGE_EXTENSION_ALLOW_LIST:
        # by the time custom validations are called, file upload handlers have
        # already done their job and the file is in S3, so we have to delete it
        delete_file_from_s3(file.name)

        raise forms.ValidationError(
            "Invalid file extension. Only these extensions are allowed: "
            + ", ".join(IMAGE_EXTENSION_ALLOW_LIST)
        )


def create_file_model(
    f: S3Boto3StorageFile,
    created_by: User,
    related_file_manager: Any,
    extra_args: dict[str, Any] | None = None,
) -> models.Model:
    """Create File (or sub-class) model.

    related_file_manager is either this:
      https://docs.djangoproject.com/en/3.2/ref/models/relations/#django.db.models.fields.related.RelatedManager.create
      for ManyToMany fields (in which case this adds it to the related set as well)

    or this: https://docs.djangoproject.com/en/3.2/ref/models/querysets/#create
             for OneToOne fields
    """

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
