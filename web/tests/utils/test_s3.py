from unittest.mock import MagicMock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from web.utils import s3 as s3_web


@override_settings(AWS_STORAGE_BUCKET_NAME="Fake-Bucket")
def test_upload_file_obj_to_s3_in_parts():
    fake_file = SimpleUploadedFile("test_file.txt", b"file_content")
    fake_client = MagicMock(
        create_multipart_upload=MagicMock(return_value={"UploadId": "x12345"}),
        upload_part=MagicMock(
            side_effect=[{"ETag": "MyETag1"}, {"ETag": "MyETag2"}, {"ETag": "MyETag3"}]
        ),
        head_object=MagicMock(return_value={"ContentLength": 44444}),
    )

    s3_web.FILE_CHUNK_SIZE = 5
    actual_content_length = s3_web.upload_file_obj_to_s3_in_parts(
        fake_file, "test_file.txt", fake_client
    )
    assert actual_content_length == 44444
    fake_client.create_multipart_upload.assert_called_with(
        Bucket="Fake-Bucket", Key="test_file.txt"
    )
    assert fake_client.upload_part.call_count == 3
    fake_client.upload_part.assert_any_call(
        Bucket="Fake-Bucket", Body=b"file_", PartNumber=1, UploadId="x12345", Key="test_file.txt"
    )
    fake_client.upload_part.assert_any_call(
        Bucket="Fake-Bucket", Body=b"conte", PartNumber=2, UploadId="x12345", Key="test_file.txt"
    )
    fake_client.upload_part.assert_any_call(
        Bucket="Fake-Bucket", Body=b"nt", PartNumber=3, UploadId="x12345", Key="test_file.txt"
    )
    fake_client.complete_multipart_upload.assert_called_with(
        Bucket="Fake-Bucket",
        Key="test_file.txt",
        UploadId="x12345",
        MultipartUpload={
            "Parts": [
                {"PartNumber": 1, "ETag": "MyETag1"},
                {"PartNumber": 2, "ETag": "MyETag2"},
                {"PartNumber": 3, "ETag": "MyETag3"},
            ]
        },
    )
    fake_client.head_object.assert_called_with(Bucket="Fake-Bucket", Key="test_file.txt")


@override_settings(AWS_STORAGE_BUCKET_NAME="Fake-Bucket")
def test_upload_file_obj():
    fake_file = SimpleUploadedFile("test_file.txt", b"file_content")
    fake_client = MagicMock(
        head_object=MagicMock(return_value={"ContentLength": 44444}),
    )
    actual_content_length = s3_web.upload_file_obj_to_s3(fake_file, "test_file.txt", fake_client)
    assert actual_content_length == 44444
    fake_client.upload_fileobj.assert_called_with(
        fake_file, Bucket="Fake-Bucket", Key="test_file.txt"
    )
    fake_client.head_object.assert_called_with(Bucket="Fake-Bucket", Key="test_file.txt")
