from io import StringIO
from unittest.mock import Mock, create_autospec, mock_open, patch

import pytest
from django.core.management import call_command

import web.management.commands.generate_static_pdf as command
from web.models import File
from web.utils.pdf.utils import cfs_cover_letter_key_filename
from web.utils.s3 import upload_file_obj_to_s3


def test_generate_static_pdf_s3(db, monkeypatch):
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
        "Uploading cover letter to S3. static_documents/CFS Letter.pdf\n"
        "Fetching file object from File model.\n"
        "No file object found. Created.\n"
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
        "Uploading cover letter to S3. static_documents/CFS Letter.pdf\n"
        "Fetching file object from File model.\n"
        "Updating file object.\n"
        "Done.\n"
    )

    f = File.objects.get(path=key, filename=filename)
    assert f.file_size == 300


@patch("builtins.open", new_callable=mock_open, read_data=b"data")
def test_generate_static_pdf_disk(mock_file, db, monkeypatch):
    monkeypatch.setattr(command.Path, "mkdir", Mock())
    out = StringIO()

    call_command("generate_static_pdf", "--output=disk", stdout=out, stderr=StringIO())

    assert out.getvalue() == (
        "Generating CFS cover letter.\n"
        "Saving the pdf to output_documents.\n"
        "Saved the pdf to output_documents/CFS Letter.pdf\n"
        "Done.\n"
    )
