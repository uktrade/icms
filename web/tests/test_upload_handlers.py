import json
from http import HTTPStatus
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django_chunk_upload_handlers.s3 import FileWithVirus
from freezegun import freeze_time
from storages.backends.s3boto3 import S3Boto3StorageFile

from web.models import File
from web.tests.helpers import CaseURLS


class FakeClamAVResponse:

    def __init__(self, status: HTTPStatus, malware: bool) -> None:
        self.status = status
        self.malware = malware

    def read(self) -> str:
        return json.dumps(
            {"malware": self.malware, "reason": None if self.malware else "Virus Found"}
        )


class FakeFile:

    def __init__(self, name, *args, **kwargs) -> None:
        self.name = name
        self.size = 1
        self.content_type = "text/plain"

    @property
    def __class__(self) -> type[S3Boto3StorageFile | FileWithVirus]:
        """Setting value to S3Boto3StorageFile results in isinstance(obj, S3Boto3StorageFile) returning true"""
        if self.name == "virus":
            return FileWithVirus
        return S3Boto3StorageFile

    def close(self) -> None:
        return

    def readline(self) -> str:
        return ""


@freeze_time("2024-01-01 14:00:00")
@override_settings(
    FILE_UPLOAD_HANDLERS=[
        "django_chunk_upload_handlers.clam_av.ClamAVFileUploadHandler",
        "web.upload_handlers.S3FileUploadHandler",
    ],
    AWS_STORAGE_BUCKET_NAME="main-bucket",
    AWS_TMP_STORAGE_BUCKET_NAME="tmp-bucket",
)
@mock.patch("web.utils.s3.delete_file_from_s3")
@mock.patch("django_chunk_upload_handlers.s3.S3Boto3StorageFile")
@mock.patch("django_chunk_upload_handlers.s3.boto3_client")
@mock.patch("django_chunk_upload_handlers.clam_av.HTTPSConnection")
@mock.patch("web.domains.case.utils.get_file_from_s3")
def test_upload_virus_free_file(
    mock_get_file_from_s3,
    mock_clam_av_connection,
    mock_boto_client,
    mock_boto_storage_file,
    mock_delete_file_from_s3_from_s3,
    completed_dfl_app_with_supplementary_report,
    importer_client,
):
    mock_delete_file_from_s3_from_s3.return_value = None
    mock_boto_client.return_value = mock.MagicMock()
    mock_boto_storage_file.return_value = FakeFile("ss.png")
    mock_clam_av_connection.return_value.getresponse.return_value = FakeClamAVResponse(
        HTTPStatus.OK, False
    )
    mock_clam_av_connection.return_value.connect.return_value = None
    mock_get_file_from_s3.return_value = b"test_file"

    app = completed_dfl_app_with_supplementary_report
    _upload_file(app, importer_client)

    assert mock_boto_client.call_count == 1
    assert mock_boto_storage_file.call_count == 1
    assert mock_get_file_from_s3.call_count == 1
    assert mock_clam_av_connection.call_count == 1
    assert mock_delete_file_from_s3_from_s3.call_count == 0

    assert str(mock_boto_client.mock_calls[-1]).startswith("call().copy_object(")
    assert mock_boto_client.mock_calls[-1].kwargs == {
        "Bucket": "tmp-bucket",
        "ContentType": "text/plain",
        "CopySource": "main-bucket/virusfree_20240101140000.png",
        "Key": "virusfree_20240101140000.png",
        "MetadataDirective": "COPY",
    }


@freeze_time("2024-01-01 14:00:00")
@override_settings(
    FILE_UPLOAD_HANDLERS=[
        "django_chunk_upload_handlers.clam_av.ClamAVFileUploadHandler",
        "web.upload_handlers.S3FileUploadHandler",
    ],
    AWS_STORAGE_BUCKET_NAME="main-bucket",
    AWS_TMP_STORAGE_BUCKET_NAME="tmp-bucket",
)
@mock.patch("web.domains.file.utils.delete_file_from_s3")
@mock.patch("django_chunk_upload_handlers.s3.S3Boto3StorageFile")
@mock.patch("django_chunk_upload_handlers.s3.boto3_client")
@mock.patch("django_chunk_upload_handlers.clam_av.HTTPSConnection")
@mock.patch("web.domains.case.utils.get_file_from_s3")
def test_upload_file_with_virus(
    mock_get_file_from_s3,
    mock_clam_av_connection,
    mock_boto_client,
    mock_boto_storage_file,
    mock_delete_file_from_s3_from_s3,
    completed_dfl_app_with_supplementary_report,
    importer_client,
):
    mock_delete_file_from_s3_from_s3.return_value = None
    mock_boto_client.return_value = mock.MagicMock()
    mock_boto_storage_file.return_value = FakeFile("ss.png")
    mock_clam_av_connection.return_value.getresponse.return_value = FakeClamAVResponse(
        HTTPStatus.OK, True
    )
    mock_clam_av_connection.return_value.connect.return_value = None
    mock_get_file_from_s3.return_value = b"test_file"

    app = completed_dfl_app_with_supplementary_report
    _upload_file_error(app, importer_client)

    assert mock_boto_client.call_count == 1
    assert mock_boto_storage_file.call_count == 0
    assert mock_get_file_from_s3.call_count == 0
    assert mock_clam_av_connection.call_count == 1
    assert mock_delete_file_from_s3_from_s3.call_count == 1

    assert str(mock_boto_client.mock_calls[-1]).startswith("call().delete_object(")
    assert mock_boto_client.mock_calls[-1].kwargs == {
        "Bucket": "",
        "Key": "myimage_20240101140000.png",
    }


def _upload_file(app, importer_client):
    report = app.supplementary_info.reports.first()
    goods_certificate = report.get_goods_certificates().first()

    url = CaseURLS.fa_dfl_report_upload_add(app.pk, report.pk, goods_certificate.pk)
    resp = importer_client.post(
        url,
        data={"file": SimpleUploadedFile("virusfree.png", b"file_content")},
    )
    assert resp.status_code == HTTPStatus.FOUND

    new_report = report.firearms.last()
    url = CaseURLS.fa_dfl_report_view_document(app.pk, report.pk, new_report.pk)
    resp = importer_client.get(url)
    assert resp.status_code == HTTPStatus.OK
    assert resp.headers["Content-Disposition"] == 'attachment; filename="virusfree.png"'

    assert File.objects.last().clam_av_results == [
        {
            "av_passed": True,
            "file_name": "virusfree.png",
            "scanned_at": "2024-01-01T14:00:00Z",
        },
    ]


def _upload_file_error(app, importer_client):
    report = app.supplementary_info.reports.first()
    goods_certificate = report.get_goods_certificates().first()
    url = CaseURLS.fa_dfl_report_upload_add(app.pk, report.pk, goods_certificate.pk)
    resp = importer_client.post(
        url,
        data={"file": SimpleUploadedFile("myimage.png", b"file_content")},
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.context["form"].errors == {
        "file": [
            "A virus was found",
            "Invalid file extension. Only these extensions are allowed: bmp, csv, doc, docx, dotx, eml, gif, heic, "
            "jfif, jpeg, jpg, msg, odt, pdf, png, rtf, tif, tiff, txt, xls, xlsb, xlsx, xps",
        ]
    }
