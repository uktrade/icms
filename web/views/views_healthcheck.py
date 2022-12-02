import time
from collections.abc import Callable, Iterable
from typing import NamedTuple

from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse

from web.models import Importer


class CheckResult(NamedTuple):
    success: bool
    # having this seems like a security problem
    # error_msg: str


PINGDOM_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<pingdom_http_custom_check>
    <status>{status}</status>
    <response_time>{response_time}</response_time>
</pingdom_http_custom_check>\n"""

COMMENT_TEMPLATE = "<!--{comment}-->\n"


def check_database() -> CheckResult:
    try:
        Importer.objects.all().exists()

        return CheckResult(
            success=True,
            # error_msg=""
        )

    except DatabaseError as e:
        print(e)
        return CheckResult(
            success=False,
            # error_msg=str(e)
        )


def get_services_to_check() -> Iterable[Callable[[], CheckResult]]:
    return (check_database,)


def health_check(request: HttpRequest) -> HttpResponse:
    t = time.time()
    results = [service() for service in get_services_to_check()]

    t = time.time() - t

    # pingdom can only accept 3 fractional digits
    t_str = "%.3f" % t

    if all(item.success for item in results):
        return HttpResponse(
            PINGDOM_TEMPLATE.format(status="OK", response_time=t_str), content_type="text/xml"
        )
    else:
        return HttpResponse(
            PINGDOM_TEMPLATE.format(status="FALSE", response_time=t_str),
            status=500,
            content_type="text/xml",
        )
