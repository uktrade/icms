import time
from collections.abc import Callable

from botocore.client import ClientError
from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse

from web.models import Importer
from web.utils.s3 import get_s3_client


def check_database() -> bool:
    try:
        Importer.objects.all().exists()

        return True

    except DatabaseError:
        return False


def check_s3() -> bool:
    client = get_s3_client()

    try:
        # From the client docs:
        # You can use this operation to determine if a bucket exists and if you have permission to
        # access it.
        client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
    except ClientError:
        return False

    return True


def check_redis() -> bool:
    try:
        cache.set("test_redis_key", "test_redis_value", timeout=1)
    except Exception:
        return False

    return True


def get_services_to_check() -> list[Callable[[], bool]]:
    return [check_database, check_s3, check_redis]


PINGDOM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<pingdom_http_custom_check>
    <status>{status}</status>
    <response_time>{response_time}</response_time>
</pingdom_http_custom_check>\n"""

COMMENT_TEMPLATE = "<!--{comment}-->\n"


def health_check(request: HttpRequest) -> HttpResponse:
    t = time.time()

    failed = [check_func.__name__ for check_func in get_services_to_check() if not check_func()]

    t = time.time() - t

    # pingdom can only accept 3 fractional digits
    t_str = "%.3f" % t

    if not failed:
        return HttpResponse(
            PINGDOM_TEMPLATE.format(status="OK", response_time=t_str), content_type="text/xml"
        )
    else:
        body = PINGDOM_TEMPLATE.format(status="FALSE", response_time=t_str)

        for check_name in failed:
            body += COMMENT_TEMPLATE.format(comment=f"The following check failed: {check_name}")

        return HttpResponse(body, status=500, content_type="text/xml")
