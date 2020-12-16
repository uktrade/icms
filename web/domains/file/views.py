import structlog as logging
from django.conf import settings
from s3chunkuploader.file_handler import s3_client
from sentry_sdk import capture_exception

from web.utils import FilevalidationService
from web.utils.s3upload import InvalidFileException, S3UploadService
from web.utils.virus import ClamAV, InfectedFileException

logger = logging.get_logger(__name__)


def handle_uploaded_file(f, created_by, related_file_model):
    file_path = None
    error_message = None
    try:
        upload_service = S3UploadService(
            s3_client=s3_client(),
            virus_scanner=ClamAV(
                settings.CLAM_AV_USERNAME, settings.CLAM_AV_PASSWORD, settings.CLAM_AV_URL
            ),
            file_validator=FilevalidationService(),
        )

        file_path = upload_service.process_uploaded_file(settings.AWS_STORAGE_BUCKET_NAME, f)
    except (InvalidFileException, InfectedFileException) as e:
        error_message = str(e)
    except Exception as e:
        capture_exception(e)
        logger.exception(e)
        error_message = "Unknown error uploading file"
    finally:
        return related_file_model.create(
            filename=f.original_name,
            file_size=f.file_size,
            content_type=f.content_type,
            browser_content_type=f.content_type,
            error_message=error_message,
            path=file_path,
            created_by=created_by,
        )
