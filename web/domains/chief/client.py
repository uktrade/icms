import typing
from urllib.parse import urljoin

import mohawk
import requests
from django.conf import settings

from web.domains.chief.views import seen_nonce

HTTPMethod = typing.Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"]


def make_hawk_sender(method: HTTPMethod, url: str, **kwargs) -> mohawk.Sender:
    creds = {
        "id": settings.HAWK_AUTH_ID,
        "key": settings.HAWK_AUTH_KEY,
        "algorithm": "sha256",
    }

    return mohawk.Sender(creds, url, method, **kwargs)


def make_request(method: HTTPMethod, url: str, **kwargs) -> tuple[mohawk.Sender, requests.Response]:
    # Requests allows calling with a dict which is converted to a JSON body,
    # but we need the final body and type to create the Hawk signature, which
    # is then added as an auth header to the request.
    request = requests.Request(method, url, **kwargs)
    prepped = request.prepare()

    if prepped.body:
        kwargs = {
            "content": prepped.body,
            "content_type": prepped.headers["Content-type"],
        }
    else:
        kwargs = {"always_hash_content": False}

    hawk_sender = make_hawk_sender(method, url, seen_nonce=seen_nonce, **kwargs)
    prepped.headers["Authorization"] = hawk_sender.request_header
    prepped.headers["Hawk-Authentication"] = hawk_sender.request_header

    session = requests.Session()
    response = session.send(prepped)

    return hawk_sender, response


def request_license(data: dict, check_response=True) -> requests.Response:
    """Send data as JSON to icms-hmrc's CHIEF end-point, signed by Hawk auth."""

    url = urljoin(settings.ICMS_HMRC_DOMAIN, settings.ICMS_HMRC_UPDATE_LICENCE_ENDPOINT)
    hawk_sender, response = make_request("POST", url, json=data)

    # TODO: ICMSLST-1628 Remove this before completing
    if check_response:
        response.raise_for_status()

    # Verify the response signature.
    server_auth = response.headers["Server-authorization"]
    hawk_sender.accept_response(
        server_auth, content=response.content, content_type=response.headers["Content-type"]
    )

    return response
