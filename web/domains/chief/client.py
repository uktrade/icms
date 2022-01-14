import typing

import mohawk
import requests
from django.conf import settings

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
    hawk_sender = make_hawk_sender(
        method, url, content=prepped.body, content_type=prepped.headers["Content-type"]
    )
    prepped.headers["Authorization"] = hawk_sender.request_header
    session = requests.Session()
    response = session.send(prepped)

    return hawk_sender, response


def request_license(data: dict) -> requests.Response:
    """Send data as JSON to icms-hmrc's CHIEF end-point, signed by Hawk auth."""
    url = settings.CHIEF_LICENSE_URL
    hawk_sender, response = make_request("POST", url, json=data)
    response.raise_for_status()

    # Verify the response signature.
    server_auth = response.headers["Server-authorization"]
    hawk_sender.accept_response(
        server_auth, content=response.content, content_type=response.headers["Content-type"]
    )

    return response
