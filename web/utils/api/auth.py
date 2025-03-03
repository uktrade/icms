import http
from typing import Any, ClassVar, Literal

import mohawk
import mohawk.exc
import pydantic
import requests
from django.conf import settings
from django.core import exceptions
from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from mohawk.util import parse_authorization_header, prepare_header_val

from web.utils.sentry import capture_exception

HTTPMethod = Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"]
APIType = Literal["hmrc", "data_workspace"]

HAWK_RESPONSE_HEADER = "Server-Authorization"
HAWK_NONCE_EXPIRY = 60  # seconds
NONCE_CACHE_PREFIX = "hawk-nonce"


def seen_nonce(access_id: str, nonce: str, timestamp: str) -> bool:
    """True if this nonce has been used already."""
    key = f"{NONCE_CACHE_PREFIX}:{access_id}:{nonce}"
    # Returns True if the key/value was added, False if it already existed. So
    # we want to return False if the key/value was added, True if it existed.
    value_was_stored = cache.add(key, timestamp, timeout=HAWK_NONCE_EXPIRY)

    return not value_was_stored


def get_credentials_map(access_id: str) -> dict[str, Any]:
    try:
        credentials = settings.HAWK_CREDENTIALS[access_id]
    except KeyError as exc:
        raise mohawk.exc.HawkFail(f"No Hawk ID of {access_id}") from exc

    return credentials


def get_hmrc_credentials(access_id: str) -> dict[str, Any]:
    hawk_auth_id = settings.HAWK_ICMS_HMRC_API_ID
    if not constant_time_compare(access_id, hawk_auth_id):
        raise mohawk.exc.HawkFail(f"Invalid Hawk ID {access_id}")
    return get_credentials_map(access_id)


def get_data_workspace_credentials(access_id: str) -> dict[str, Any]:
    hawk_auth_id = settings.HAWK_DATA_WORKSPACE_API_ID
    if not constant_time_compare(access_id, hawk_auth_id):
        raise mohawk.exc.HawkFail(f"Invalid Hawk ID {access_id}")
    return get_credentials_map(access_id)


def validate_request(request: HttpRequest, api_type: APIType) -> mohawk.Receiver:
    """Raise Django's BadRequest if the request has invalid credentials."""

    try:
        auth_token = request.headers.get("HAWK_AUTHENTICATION")

        if not auth_token:
            raise KeyError
    except KeyError as err:
        raise exceptions.BadRequest from err

    match api_type:
        case "hmrc":
            credentials_func = get_hmrc_credentials
        case "data_workspace":
            credentials_func = get_data_workspace_credentials
        case _:
            raise ValueError(f'Unknown api type "{api_type}"')

    # ICMS-HMRC creates the payload hash before encoding the json, therefore decode it here to get the same hash.
    content = request.body.decode()

    try:
        return mohawk.Receiver(
            credentials_func,
            auth_token,
            request.build_absolute_uri(),
            request.method,
            content=content,
            content_type=request.content_type,
            seen_nonce=seen_nonce,
        )
    except mohawk.exc.HawkFail as err:
        raise exceptions.BadRequest from err


def make_hawk_sender(
    method: HTTPMethod, url: str, api_type: APIType, **kwargs: Any
) -> mohawk.Sender:
    match api_type:
        case "hmrc":
            api_id = settings.HAWK_ICMS_HMRC_API_ID
        case "data_workspace":
            api_id = settings.HAWK_DATA_WORKSPACE_API_ID
        case _:
            raise ValueError('Incorrect api_type "{api_type}" for hawk request')

    creds = settings.HAWK_CREDENTIALS[api_id]

    return mohawk.Sender(creds, url, method, **kwargs)


def make_hawk_request(
    method: HTTPMethod, url: str, api_type: APIType, **kwargs: Any
) -> tuple[mohawk.Sender, requests.Response]:
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
        kwargs = {
            "content": "",
            # We have to have a default content_type value for hawk to work
            "content_type": prepped.headers.get("Content-type", "text/plain"),
        }

    # Use prepped.url to ensure stuff like query params are included when comparing generated MACs
    hawk_sender = make_hawk_sender(
        method,
        prepped.url,  # type:ignore[arg-type]
        api_type=api_type,
        seen_nonce=seen_nonce,
        **kwargs,
    )

    prepped.headers["Authorization"] = hawk_sender.request_header
    prepped.headers["Hawk-Authentication"] = hawk_sender.request_header

    session = requests.Session()
    response = session.send(prepped)

    return hawk_sender, response


# Hawk view (no CSRF)
@method_decorator(csrf_exempt, name="dispatch")
class HawkAuthMixin:
    hawk_api_type: ClassVar[APIType]

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            # Validate sender request
            hawk_receiver = validate_request(request, self.hawk_api_type)

            # Create response
            response = super().dispatch(request, *args, **kwargs)  # type:ignore[misc]

        except (pydantic.ValidationError, exceptions.BadRequest):
            capture_exception()

            return JsonResponse({}, status=http.HTTPStatus.BAD_REQUEST)

        except Exception:
            capture_exception()

            return JsonResponse({}, status=http.HTTPStatus.UNPROCESSABLE_ENTITY)

        # Create and set the response header
        hawk_response_header = self._get_hawk_response_header(hawk_receiver, response)
        response.headers[HAWK_RESPONSE_HEADER] = hawk_response_header

        # return the response
        return response

    def _get_hawk_response_header(
        self, hawk_receiver: mohawk.Receiver, response: JsonResponse
    ) -> str:
        sender_nonce = hawk_receiver.parsed_header.get("nonce")

        hawk_response_header = hawk_receiver.respond(
            content=response.content, content_type=response.headers["Content-type"]
        )

        # Add the original sender nonce and ts to get around this bug
        # https://github.com/kumar303/mohawk/issues/50
        if not parse_authorization_header(hawk_response_header).get("nonce"):
            sender_nonce = prepare_header_val(sender_nonce)
            ts = prepare_header_val(str(timezone.now().timestamp()))

            hawk_response_header = f'{hawk_response_header}, nonce="{sender_nonce}", ts="{ts}"'

        return hawk_response_header


class HawkHMRCMixin(HawkAuthMixin):
    hawk_api_type = "hmrc"


class HawkDataWorkspaceMixin(HawkAuthMixin):
    hawk_api_type = "data_workspace"
