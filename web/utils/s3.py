import logging
from typing import TYPE_CHECKING, Any, Optional

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

if TYPE_CHECKING:
    from mypy_boto3_s3 import Client as S3Client
    from mypy_boto3_s3 import ServiceResource as S3Resource


from web.utils.sentry import capture_exception

logger = logging.getLogger(__name__)


def _get_s3_extra_kwargs() -> dict[str, Any]:
    extra_kwargs = {}

    if settings.AWS_S3_ENDPOINT_URL:
        extra_kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL

    if hasattr(settings, "AWS_ACCESS_KEY_ID") and hasattr(settings, "AWS_SECRET_ACCESS_KEY"):
        extra_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        extra_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return extra_kwargs


def get_s3_client() -> "S3Client":
    """Get an S3 client."""
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        **_get_s3_extra_kwargs(),
    )


def get_s3_resource() -> "S3Resource":
    return boto3.resource(
        "s3",
        region_name=settings.AWS_REGION,
        **_get_s3_extra_kwargs(),
    )


def get_s3_file_count(s3_resource: "S3Resource", prefixes: list[str]) -> int:
    bucket = s3_resource.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
    count = 0
    for prefix in prefixes:
        count += len([i for i in bucket.objects.filter(Prefix=prefix)])
    return count


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


def upload_file_obj_to_s3(file_obj: Any, key: str, client: Optional["S3Client"] = None) -> int:
    """Upload file obj to s3 and return the size of the file (bytes)."""

    if not client:
        client = get_s3_client()

    client.upload_fileobj(file_obj, Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)

    object_meta = client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)

    return object_meta["ContentLength"]


def upload_file_obj_to_s3_in_parts(
    file_obj: Any, key: str, client: Optional["S3Client"] = None
) -> int:
    """Upload file obj to s3 and return the size of the file (bytes)."""
    chunk_size = 5 * 1024**2

    if not client:
        client = get_s3_client()

    response = client.create_multipart_upload(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
    upload_id = response["UploadId"]

    parts_info = []

    offset = 1
    part_number = 1
    while True:
        data = file_obj.read(offset, chunk_size)
        if data:
            part = client.upload_part(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=key,
                Body=data,
                UploadId=upload_id,
                PartNumber=part_number,
            )
            parts_info.append({"PartNumber": part_number, "ETag": part["ETag"]})
        if len(data) < chunk_size:
            break
        offset += len(data)
        part_number += 1

    client.complete_multipart_upload(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts_info},  # type: ignore
    )

    object_meta = client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)

    return object_meta["ContentLength"]


def put_object_in_s3(file_data: str | bytes, key: str, client: Optional["S3Client"] = None) -> int:
    """Uploads data as file to s3 and return the size of the file (bytes)."""

    if not client:
        client = get_s3_client()

    client.put_object(Body=file_data, Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)

    object_meta = client.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)

    return object_meta["ContentLength"]


def create_presigned_url(key: str, expiration: int = 60 * 60) -> str | None:
    """Generate a presigned URL to share an S3 object

    :param key: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = get_s3_client()
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
            ExpiresIn=expiration,
        )
    except ClientError:
        capture_exception()
        return None

    if response.startswith("http://localstack"):
        response = response.replace("http://localstack", "http://localhost")

    # The response is the presigned URL
    return response
