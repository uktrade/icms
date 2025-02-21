import json
import logging
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.utils import timezone

from web.domains.case.shared import ImpExpStatus
from web.flow.models import ProcessTypes
from web.models import ICMSHMRCChiefRequest, Task
from web.utils.api.auth import make_hawk_request
from web.utils.sentry import capture_exception

from . import serializers, types

if TYPE_CHECKING:
    from web.models import ImportApplication

logger = logging.getLogger(__name__)


def send_application_to_chief(
    application: "ImportApplication", previous_task: Task | None, revoke_licence: bool = False
) -> None:
    """Sends licence data to CHIEF if enabled.

    Sends INSERT, REPLACE & CANCEL records.
    """

    chief_req = None
    if revoke_licence:
        next_task = Task.TaskType.CHIEF_REVOKE_WAIT
    else:
        next_task = Task.TaskType.CHIEF_WAIT

    try:
        if settings.SEND_LICENCE_TO_CHIEF:
            action: serializers.CHIEF_ACTION
            if revoke_licence:
                action = "cancel"
            elif application.status == ImpExpStatus.VARIATION_REQUESTED:
                action = "replace"
            else:
                action = "insert"

            logger.debug(
                "Sending application with reference %r to chief with action %r",
                application.reference,
                action,
            )

            chief_req = ICMSHMRCChiefRequest.objects.create(
                import_application=application,
                case_reference=application.reference,
                request_sent_datetime=timezone.now(),
            )
            serialize = get_serializer(application.process_type, action)
            data = serialize(application.get_specific_model(), action, str(chief_req.icms_hmrc_id))

            # Django JSONField encodes python objects therefore data.model_dump_json() can't be used
            chief_req.request_data = data.model_dump()
            chief_req.save()

            request_license(data)

        else:
            # Create a dummy one for testing
            logger.debug("Faking chief request for application %r", application.reference)
            chief_req = ICMSHMRCChiefRequest.objects.create(
                import_application=application,
                case_reference=application.reference,
                request_data={"foo": "bar", "test": "data"},
                request_sent_datetime=timezone.now(),
            )

    except Exception as e:
        capture_exception()
        next_task = Task.TaskType.CHIEF_ERROR

        if chief_req:
            chief_req.status = ICMSHMRCChiefRequest.CHIEFStatus.INTERNAL_ERROR

            if isinstance(e, requests.HTTPError):
                try:
                    if errors := e.response.json().get("errors"):
                        for error in errors:
                            chief_req.response_errors.create(
                                error_code=e.response.status_code, error_msg=json.dumps(error)
                            )

                # It doesn't have the expected "errors" key
                except requests.JSONDecodeError:
                    pass

            chief_req.save()

    Task.objects.create(process=application, task_type=next_task, previous=previous_task)


def get_serializer(
    process_type: str, action: serializers.CHIEF_ACTION
) -> serializers.ChiefSerializer:
    if action == "cancel":
        return serializers.cancel_licence_serializer

    match process_type:
        case ProcessTypes.FA_OIL:
            return serializers.fa_oil_serializer
        case ProcessTypes.FA_DFL:
            return serializers.fa_dfl_serializer
        case ProcessTypes.FA_SIL:
            return serializers.fa_sil_serializer
        case ProcessTypes.SANCTIONS:
            return serializers.sanction_serializer
        case _:
            raise NotImplementedError(f"Unsupported process_type: {process_type}")


def request_license(data: types.LicenceDataPayload) -> requests.Response:
    """Send data as JSON to icms-hmrc's CHIEF end-point, signed by Hawk auth."""

    url = urljoin(settings.ICMS_HMRC_DOMAIN, settings.ICMS_HMRC_UPDATE_LICENCE_ENDPOINT)

    hawk_sender, response = make_hawk_request(
        "POST", url, data=data.model_dump_json(), headers={"Content-Type": "application/json"}
    )

    # log the response in case `raise_for_status` throws an error
    # Enable this line if there are issues sending data to icms-hmrc
    # logger.info(str(response.content))

    response.raise_for_status()

    # Verify the response signature.
    server_auth = response.headers["Server-authorization"]
    hawk_sender.accept_response(
        server_auth, content=response.content, content_type=response.headers["Content-type"]
    )

    return response
