from typing import Any

import boto3
from django.conf import settings


def get_s3_client() -> Any:
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


def get_file_from_s3(path: str, client: Any = None) -> bytes:
    """Get contents of an object in S3."""

    if not client:
        client = get_s3_client()

    s3_file = client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=path)
    contents = s3_file["Body"].read()

    return contents


def delete_file_from_s3(path: str, client: Any = None) -> None:
    """Delete object in S3."""

    if not client:
        client = get_s3_client()

    client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=path)
