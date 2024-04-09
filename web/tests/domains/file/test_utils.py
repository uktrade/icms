from random import choice
from unittest import mock

import pytest
from django.forms import forms
from storages.backends.s3boto3 import S3Boto3StorageFile

from web.domains.file.utils import (
    FILE_EXTENSION_ALLOW_LIST,
    IMAGE_EXTENSION_ALLOW_LIST,
    ImageFileFieldValidator,
    validate_file_extension,
)


@pytest.mark.parametrize(
    ["file_extension"], [(extension,) for extension in FILE_EXTENSION_ALLOW_LIST]
)
def test_validate_file_extension_valid(file_extension):
    with mock.create_autospec(S3Boto3StorageFile) as mock_file:
        # test lowercase
        mock_file.name = f"foo.{file_extension.lower()}"
        validate_file_extension(mock_file)

        # Test uppercase
        mock_file.name = f"foo.{file_extension.upper()}"
        validate_file_extension(mock_file)

        # Test random case
        mock_file.name = "".join(choice([str.upper, str.lower])(c) for c in mock_file.name)
        validate_file_extension(mock_file)


@pytest.mark.parametrize(
    ["file_extension"],
    [
        ("bat",),
        ("bin",),
        ("com",),
        ("dll",),
        ("exe",),
        ("htm",),
        ("html",),
        ("msc",),
        ("msi",),
        ("msp",),
        ("ocx",),
        ("scr",),
        ("wsc",),
        ("wsf",),
        ("wsh",),
    ],
)
def test_validate_file_extension_invalid(file_extension):
    with (
        mock.create_autospec(S3Boto3StorageFile) as mock_file,
        mock.patch("web.domains.file.utils.delete_file_from_s3") as patched_delete_file_from_s3,
    ):
        mock_file.name = f"foo.{file_extension}"

        with pytest.raises(
            forms.ValidationError,
            match="Invalid file extension. Only these extensions are allowed: ",
        ):
            validate_file_extension(mock_file)

        assert patched_delete_file_from_s3.called is True
        assert patched_delete_file_from_s3.call_args == mock.call(mock_file.name)


@pytest.mark.parametrize(
    ["file_extension"], [(extension,) for extension in IMAGE_EXTENSION_ALLOW_LIST]
)
def test_validate_image_file_extension_valid(file_extension):
    with mock.create_autospec(S3Boto3StorageFile) as mock_file:
        mock_file.name = f"foo.{file_extension}"

        # test lowercase
        mock_file.name = f"foo.{file_extension.lower()}"
        ImageFileFieldValidator()(mock_file)

        # Test uppercase
        mock_file.name = f"foo.{file_extension.upper()}"
        ImageFileFieldValidator()(mock_file)

        # Test random case
        mock_file.name = "".join(choice([str.upper, str.lower])(c) for c in mock_file.name)
        ImageFileFieldValidator()(mock_file)


@pytest.mark.parametrize(
    ["file_extension"],
    [
        ("gif",),
        ("tiff",),
        ("bmp",),
    ],
)
def test_validate_image_file_extension_invalid(file_extension):
    with (
        mock.create_autospec(S3Boto3StorageFile) as mock_file,
        mock.patch("web.domains.file.utils.delete_file_from_s3") as patched_delete_file_from_s3,
    ):
        mock_file.name = f"foo.{file_extension}"

        with pytest.raises(
            forms.ValidationError,
            match="Invalid file extension. Only these extensions are allowed: ",
        ):
            ImageFileFieldValidator()(mock_file)

        assert patched_delete_file_from_s3.called is True
        assert patched_delete_file_from_s3.call_args == mock.call(mock_file.name)


def test_validate_image_file_extension_valid_with_custom_allowed_extensions():
    with (
        mock.create_autospec(S3Boto3StorageFile) as mock_file,
        mock.patch("web.domains.file.utils.delete_file_from_s3") as patched_delete_file_from_s3,
    ):
        mock_file.name = "foo.bmp"

        ImageFileFieldValidator(allowed_extensions=["bmp"])(mock_file)

        assert patched_delete_file_from_s3.called is False


def test_validate_image_file_extension_invalid_with_custom_allowed_extensions():
    with (
        mock.create_autospec(S3Boto3StorageFile) as mock_file,
        mock.patch("web.domains.file.utils.delete_file_from_s3"),
    ):
        mock_file.name = "foo.bmp"

        with pytest.raises(
            forms.ValidationError,
            match="Invalid file extension. Only these extensions are allowed: ",
        ):
            ImageFileFieldValidator(allowed_extensions=["jpg"])(mock_file)
