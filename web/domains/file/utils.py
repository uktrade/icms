import os.path
from collections.abc import Callable, Iterable
from typing import Any

from django import forms
from django.conf import settings
from django.db import models
from django.template.loader import render_to_string
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

HELP_TEXT = "Compatible file types include " + ", ".join(FILE_EXTENSION_ALLOW_LIST)

IMAGE_EXTENSION_ALLOW_LIST = ("jpeg", "jpg", "png")

IMAGE_HELP_TEXT = "Only the following file extensions (types) are allowed to be uploaded: "

VALIDATOR = Callable[[S3Boto3StorageFile], None]


class ICMSFileField(forms.FileField):
    # Used to tell the template to render the help_text as safe
    mark_help_text_safe = True

    def __init__(
        self, *, validators: Iterable[VALIDATOR] = (), help_text: str = HELP_TEXT, **kwargs: Any
    ) -> None:
        field_help_text = render_to_string(
            template_name="forms/icms_file_field_helptext.html",
            context={
                "help_text": help_text,
                "ilb_contact_email": settings.ILB_CONTACT_EMAIL,
            },
        )

        super().__init__(
            # order is important: validate_file_extension can delete the file
            # from S3, so has to be after the virus check
            validators=[validate_virus_check_result, validate_file_extension, *validators],
            help_text=field_help_text,
            **kwargs,
        )


class ImageFileFieldValidator:
    def __init__(self, allowed_extensions: Iterable[str] = IMAGE_EXTENSION_ALLOW_LIST) -> None:
        self.allowed_extensions = allowed_extensions

    def __call__(self, file: S3Boto3StorageFile) -> None:
        """Django validator that only allows specific image file extensions."""

        _, file_extension = os.path.splitext(file.name)

        if file_extension.lstrip(".").lower() not in self.allowed_extensions:
            # by the time custom validations are called, file upload handlers have
            # already done their job and the file is in S3, so we have to delete it
            delete_file_from_s3(file.name)

            raise forms.ValidationError(
                "Invalid file extension. Only these extensions are allowed: "
                + ", ".join(self.allowed_extensions)
            )


class ImageFileField(forms.FileField):
    def __init__(
        self,
        *,
        validators: Iterable[VALIDATOR] = (),
        allowed_extensions: Iterable[str] = IMAGE_EXTENSION_ALLOW_LIST,
        help_text: str | None = None,
        **kwargs: Any,
    ) -> None:
        validate_image_file_extension = ImageFileFieldValidator(allowed_extensions)
        help_text = help_text or IMAGE_HELP_TEXT + ", ".join(allowed_extensions)
        super().__init__(
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
