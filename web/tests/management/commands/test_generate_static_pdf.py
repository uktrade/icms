from io import StringIO
from unittest.mock import create_autospec

import pytest
from django.core.management import call_command

import web.management.commands.generate_static_pdf as command
from web.models import File
from web.utils.pdf.utils import cfs_cover_letter_key_filename
from web.utils.s3 import upload_file_obj_to_s3


def test_generate_static_pdf(db, monkeypatch):
    key, filename = cfs_cover_letter_key_filename()

    with pytest.raises(File.DoesNotExist):
        File.objects.get(path=key, filename=filename)

    upload_file_obj_to_s3_mock = create_autospec(upload_file_obj_to_s3)
    upload_file_obj_to_s3_mock.return_value = 1000
    monkeypatch.setattr(command, "upload_file_obj_to_s3", upload_file_obj_to_s3_mock)
    out = StringIO()

    call_command("generate_static_pdf", stdout=out, stderr=StringIO())

    assert out.getvalue() == (
        "Generating CFS cover letter.\n"
        "Uploading cover letter to S3.\n"
        "Fetching file object from File model.\n"
        "No file object found. Creating.\n"
        "Done.\n"
    )

    f = File.objects.get(path=key, filename=filename)
    assert f.file_size == 1000

    upload_file_obj_to_s3_mock.return_value = 300
    monkeypatch.setattr(command, "upload_file_obj_to_s3", upload_file_obj_to_s3_mock)
    out = StringIO()

    call_command("generate_static_pdf", stdout=out, stderr=StringIO())

    assert out.getvalue() == (
        "Generating CFS cover letter.\n"
        "Uploading cover letter to S3.\n"
        "Fetching file object from File model.\n"
        "Updating file object.\n"
        "Done.\n"
    )

    f = File.objects.get(path=key, filename=filename)
    assert f.file_size == 300
