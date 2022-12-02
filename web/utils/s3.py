import logging
from typing import IO, TYPE_CHECKING, Any, Optional

import boto3
from django.conf import settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import Client as S3Client

logger = logging.getLogger(__name__)


def get_s3_client() -> "S3Client":
    """Get an S3 client."""
    extra_kwargs = {}

    if settings.AWS_S3_ENDPOINT_URL:
        extra_kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL

    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
        **extra_kwargs,
    )


def get_file_from_s3(path: str, client: Optional["S3Client"] = None) -> bytes:
    """Get contents of an object in S3."""

    if not client:
        client = get_s3_client()

    s3_file = client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=path)
    contents = s3_file["Body"].read()

    return contents


def delete_file_from_s3(path: str, client: Optional["S3Client"] = None) -> None:
    """Delete object in S3."""

    if not client:
        client = get_s3_client()

    client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=path)
    logger.debug("Removed file from S3: %s.", path)


def upload_file_obj_to_s3(file_obj: IO[Any], key: str, client: Optional["S3Client"] = None) -> int:
    """Upload file obj to s3 and return the size of the file (bytes)."""

    if not client:
        client = get_s3_client()

    client.upload_fileobj(file_obj, Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)

    object_meta = client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)

    return object_meta["ContentLength"]
