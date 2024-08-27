from django.core.files.uploadedfile import UploadedFile
from django_chunk_upload_handlers.clam_av import (
    FileWithVirus,
    VirusFoundInFileException,
)
from django_chunk_upload_handlers.s3 import AWS_STORAGE_BUCKET_NAME
from django_chunk_upload_handlers.s3 import (
    S3FileUploadHandler as DjangoChunkS3FileUploadHandler,
)


class S3FileUploadHandler(DjangoChunkS3FileUploadHandler):
    """A custom S3FileUploadHandler that permanently deletes virus-infected files from S3 even when versioning
    is enabled on the bucket.
    """

    def file_complete(self, file_size: int) -> UploadedFile:
        # we wrap this in a try/except and also check if the file is a FileWithVirus in case
        # CHUNK_UPLOADER_RAISE_EXCEPTION_ON_VIRUS_FOUND is set to True for whatever reason - we need to be sure.
        try:
            file = super().file_complete(file_size)
            if isinstance(file, FileWithVirus):
                # permanently delete the virus-infected file from S3
                self.permanently_delete_file()

            return file
        except VirusFoundInFileException:
            self.permanently_delete_file()
            raise

    def permanently_delete_file(self) -> None:
        paginator = self.s3_client.get_paginator("list_object_versions")
        response_iterator = paginator.paginate(Bucket=AWS_STORAGE_BUCKET_NAME)
        for response in response_iterator:
            versions = response.get("Versions", [])
            versions.extend(response.get("DeleteMarkers", []))
            for version_id in [
                x["VersionId"]
                for x in versions
                if x["Key"] == self.new_file_name and x["VersionId"] != "null"
            ]:
                self.s3_client.delete_object(
                    Bucket=AWS_STORAGE_BUCKET_NAME, Key=self.new_file_name, VersionId=version_id
                )
