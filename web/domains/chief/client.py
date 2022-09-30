import logging
from typing import TYPE_CHECKING, Callable, Literal, Optional
from urllib.parse import urljoin

import mohawk
import requests
from django.conf import settings
from django.utils import timezone

from web.domains.case._import.models import LiteHMRCChiefRequest
from web.domains.case.shared import ImpExpStatus
from web.domains.chief.views import seen_nonce
from web.flow.models import ProcessTypes, Task
from web.utils.sentry import capture_exception

from . import serializers, types

if TYPE_CHECKING:
    from web.models import ImportApplication

logger = logging.getLogger(__name__)

HTTPMethod = Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"]


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
        kwargs = {
            "content": "",
            # We have to have a default content_type value for hawk to work
            "content_type": prepped.headers.get("Content-type", "text/plain"),
        }

    # Use prepped.url to ensure stuff like query params are included when comparing generated MACs
    hawk_sender = make_hawk_sender(
        method, prepped.url, seen_nonce=seen_nonce, **kwargs  # type:ignore[arg-type]
    )

    prepped.headers["Authorization"] = hawk_sender.request_header
    prepped.headers["Hawk-Authentication"] = hawk_sender.request_header

    session = requests.Session()
    response = session.send(prepped)

    return hawk_sender, response


def request_license(data: types.CreateLicenceData) -> requests.Response:
    """Send data as JSON to icms-hmrc's CHIEF end-point, signed by Hawk auth."""

    url = urljoin(settings.ICMS_HMRC_DOMAIN, settings.ICMS_HMRC_UPDATE_LICENCE_ENDPOINT)

    hawk_sender, response = make_request(
        "POST", url, data=data.json(), headers={"Content-Type": "application/json"}
    )

    # TODO: ICMSLST-1660 Remove this when chief integration is finished
    # log the response in case `raise_for_status` throws an error
    logger.info(str(response.content))

    response.raise_for_status()

    # Verify the response signature.
    server_auth = response.headers["Server-authorization"]
    hawk_sender.accept_response(
        server_auth, content=response.content, content_type=response.headers["Content-type"]
    )

    return response


def send_application_to_chief(
    application: "ImportApplication", previous_task: Optional[Task]
) -> None:
    """Sends licence data to CHIEF if enabled."""

    chief_req = None
    next_task = Task.TaskType.CHIEF_WAIT

    try:
        if settings.SEND_LICENCE_TO_CHIEF:
            # TODO: Revisit when implementing ICMSLST-1762
            if application.status == ImpExpStatus.VARIATION_REQUESTED:
                # Having looked at lite-hmrc we need to create a new lite_hmrc_id each time.
                # CHIEF licence ingest view
                # if data["action"] == LicenceActionEnum.UPDATE:
                #     data["old_reference"] = LicenceIdMapping.objects.get(lite_id=data["old_id"]).reference

                # 1. get lite_chief_id from the latest LiteHMRCChiefRequests record for this application.
                # 2. Create a new record and serialise the data
                # 3. Include the old lite_chief_id in the request data

                raise NotImplementedError

            chief_req = LiteHMRCChiefRequest.objects.create(
                import_application=application,
                case_reference=application.reference,
                request_sent_datetime=timezone.now(),
            )
            serialize = get_serializer(application.process_type)
            data = serialize(application.get_specific_model(), str(chief_req.lite_hmrc_id))

            # Django JSONField encodes python objects therefore data.json() can't be used
            chief_req.request_data = data.dict()
            chief_req.save()

            request_license(data)

    except Exception:
        capture_exception()
        next_task = Task.TaskType.CHIEF_ERROR

        if chief_req:
            chief_req.delete()

    Task.objects.create(process=application, task_type=next_task, previous=previous_task)


def get_serializer(
    process_type: str,
) -> Callable[["ImportApplication", str], types.CreateLicenceData]:
    serializer_map = {
        ProcessTypes.FA_OIL: serializers.fa_oil_serializer,  # type: ignore[dict-item]
        ProcessTypes.FA_DFL: serializers.fa_dfl_serializer,  # type: ignore[dict-item]
        ProcessTypes.FA_SIL: serializers.fa_sil_serializer,  # type: ignore[dict-item]
        ProcessTypes.SANCTIONS: serializers.sanction_serializer,  # type: ignore[dict-item]
    }

    return serializer_map[process_type]  # type: ignore[index]
