from django_chunk_upload_handlers.s3 import (
    S3FileUploadHandler as DjangoChunkS3FileUploadHandler,
)
from django_chunk_upload_handlers.util import check_required_setting
from storages.backends.s3boto3 import S3Boto3StorageFile

AWS_STORAGE_BUCKET_NAME = check_required_setting(
    "AWS_TMP_STORAGE_BUCKET_NAME",
    "AWS_STORAGE_BUCKET_NAME",
)

AWS_MAIN_STORAGE_BUCKET_NAME = check_required_setting("AWS_STORAGE_BUCKET_NAME")

CHUNK_UPLOADER_RAISE_EXCEPTION_ON_VIRUS_FOUND = False


class S3FileUploadHandler(DjangoChunkS3FileUploadHandler):

    def file_complete(self, file_size: int) -> S3Boto3StorageFile:
        file = super().file_complete(file_size)
        file.content_type_extra = self.content_type_extra
        if isinstance(file, S3Boto3StorageFile):
            self.move_file_to_permanent_storage()
        return file

    def move_file_to_permanent_storage(self) -> None:
        if AWS_STORAGE_BUCKET_NAME and AWS_STORAGE_BUCKET_NAME != AWS_MAIN_STORAGE_BUCKET_NAME:
            self.s3_client.copy_object(
                Bucket=AWS_STORAGE_BUCKET_NAME,
                CopySource=f"{AWS_MAIN_STORAGE_BUCKET_NAME}/{self.new_file_name}",
                Key=self.new_file_name,
                ContentType=self.content_type,
                MetadataDirective="COPY",
            )
