from unittest.mock import MagicMock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from web.utils import s3 as s3_web


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
