import structlog as logging
import os
import random
import time

from django.conf import settings
from web.utils.virus import InfectedFileException
from web.utils import url_path_join

logger = logging.getLogger(__name__)


def random_file_name(request, original_file_name, random_salt_max=10000):
    """
    Generates a random/unique file name for a file


    Returns:
        String - a filename in the format <microsenconds since epoch>_<ranbon number>.<file_extension>
    """
    file_name, file_extension = os.path.splitext(original_file_name)
    miliseconds = int(round(time.time() * 1000))
    salt = random.randint(0, random_salt_max)

    return url_path_join(
        getattr(settings, 'S3_DOCUMENT_ROOT_DIRECTORY', ''),
        f'{miliseconds}_{salt}{file_extension}'
    )


class InvalidFileException(Exception):
    pass


class S3UploadService():
    """
        utilitarian class to handle file upload upload logic
    """
    def __init__(self, s3_client, virus_scanner, file_validator=None):
        """
        Initializes the class

        Arguments:
            s3_client {boto3.client} -- S3 client (to work with files on s3)
            virus_scanner {web.utils.virus.ClamAV} -- Virus Scanner
            file_validator {.FileValidator} -- Validates the uploaded file according to bussiness logic

        """
        self.s3_client = s3_client
        self.virus_scanner = virus_scanner
        self.file_validator = file_validator

    def process_uploaded_file(self, bucket, uploaded_file, destination):
        """
        Processes an uploaded file.
        1. Runs virus scan on file
        2. Validates the file according to bussiness logic
        3. if all passes moves the file to its destination

        Arguments:
            bucket {string} -- S3 bucket name
            uploaded_file {storages.backends.s3boto3.S3Boto3StorageFile} -- the file object in request.FILES
            destination {string} -- destination path (key) where to put the uploaded file

        Throws:
            InfectedFileException -- if file fails to pass virus scan
        """

        # upload to /documents/fir/<fir id>
        logger.debug('Processing Uploaded File %s' % uploaded_file.name)
        s3_file = self.s3_client.get_object(Bucket=bucket,
                                            Key=uploaded_file.name)
        s3_file_content = s3_file['Body'].read()

        try:
            if not self.virus_scanner.is_safe(s3_file_content):
                raise InfectedFileException(f"'{uploaded_file.original_name}' failed virus scanning")

            if not self.file_validator.is_valid(uploaded_file):
                raise InvalidFileException(f"'{uploaded_file.original_name}' is not an allowed file")

            # move file to final destination
            new_file_path = url_path_join(destination, os.path.basename(uploaded_file.name)).lstrip('/')
            self.s3_client.copy_object(
                Bucket=bucket,
                CopySource=url_path_join(bucket, uploaded_file.name),
                Key=new_file_path
            )

            logger.debug('NEW FILE PATH %s' % new_file_path)

            return new_file_path

        except Exception as e:
            logger.warning(str(e))
            raise e
        finally:
            # delete uploaded file as it is no longer needed.
            # it either failed validation or virus scanning or has been copied to the right place
            self.s3_client.delete_object(Bucket=bucket, Key=uploaded_file.name)
            pass
