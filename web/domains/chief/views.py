import http
from typing import Any

import mohawk
import mohawk.exc
import pydantic
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core import exceptions
from django.core.cache import cache
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.crypto import constant_time_compare
from django.views.generic import TemplateView, View

from web.domains.case._import.models import ImportApplication, LiteHMRCChiefRequest
from web.flow.models import Task
from web.utils.sentry import capture_exception

from . import types, utils

HAWK_ALGO = "sha256"
HAWK_NONCE_EXPIRY = 60  # seconds
NONCE_CACHE_PREFIX = "hawk-nonce"
HAWK_RESPONSE_HEADER = "Server-Authorization"


def get_credentials_map(access_id: str) -> dict[str, Any]:
    if not constant_time_compare(access_id, settings.HAWK_AUTH_ID):
        raise mohawk.exc.HawkFail(f"Invalid Hawk ID {access_id}")

    return {
        "id": settings.HAWK_AUTH_ID,
        "key": settings.HAWK_AUTH_KEY,
        "algorithm": HAWK_ALGO,
    }


def seen_nonce(access_id: str, nonce: str, timestamp: str) -> bool:
    """True if this nonce has been used already."""
    key = f"{NONCE_CACHE_PREFIX}:{access_id}:{nonce}"
    # Returns True if the key/value was added, False if it already existed. So
    # we want to return False if the key/value was added, True if it existed.
    value_was_stored = cache.add(key, timestamp, timeout=HAWK_NONCE_EXPIRY)

    return not value_was_stored


def validate_request(request: HttpRequest) -> mohawk.Receiver:
    """Raise Django's BadRequest if the request has invalid credentials."""
    try:
        auth_token = request.META["HTTP_AUTHORIZATION"]
    except KeyError as err:
        raise exceptions.BadRequest from err

    try:
        return mohawk.Receiver(
            get_credentials_map,
            auth_token,
            request.build_absolute_uri(),
            request.method,
            content=request.body,
            content_type=request.content_type,
            seen_nonce=seen_nonce,
        )
    except mohawk.exc.HawkFail as err:
        raise exceptions.BadRequest from err


class LicenseDataCallback(View):
    # View Config
    http_method_names = ["post"]

    def dispatch(self, *args, **kwargs) -> HttpResponse:
        # Validate sender request
        hawk_receiver = validate_request(self.request)

        # Create response
        response = super().dispatch(*args, **kwargs)

        # Create and set the response header
        hawk_response_header = hawk_receiver.respond(
            content=response.content, content_type=response.headers["Content-type"]
        )
        response.headers[HAWK_RESPONSE_HEADER] = hawk_response_header

        # return the response
        return response

    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        try:
            licence_replies = types.ChiefLicenceReplyResponseData.parse_raw(
                request.body, content_type=request.content_type
            )

        except pydantic.ValidationError:
            capture_exception()

            return JsonResponse({}, status=http.HTTPStatus.BAD_REQUEST)

        try:
            with transaction.atomic():
                for accepted in licence_replies.accepted:
                    self.accept_application(accepted)

                for rejected in licence_replies.rejected:
                    self.reject_application(rejected)

        except Exception:
            capture_exception()

            return JsonResponse({}, status=http.HTTPStatus.UNPROCESSABLE_ENTITY)

        return JsonResponse({}, status=http.HTTPStatus.OK)

    def accept_application(self, accepted_licence: types.AcceptedLicence) -> None:
        chief_req = self.get_chief_request(accepted_licence.reference)

        utils.chief_licence_reply_approve_licence(chief_req.import_application)
        utils.complete_chief_request(chief_req)

    def reject_application(self, rejected_licence: types.RejectedLicence) -> None:
        chief_req = self.get_chief_request(rejected_licence.reference)

        utils.chief_licence_reply_reject_licence(chief_req.import_application)
        utils.fail_chief_request(chief_req, rejected_licence.errors)

    @staticmethod
    def get_chief_request(reference: str) -> LiteHMRCChiefRequest:
        chief_req = (
            LiteHMRCChiefRequest.objects.select_related("import_application")
            .select_for_update()
            .get(case_reference=reference)
        )

        return chief_req


class _BaseTemplateView(PermissionRequiredMixin, TemplateView):
    permission_required = "web.ilb_admin"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        # We need the counts for each type to show in the navigation tabs.
        failed_licences = ImportApplication.objects.filter(
            tasks__task_type=Task.TaskType.CHIEF_ERROR, tasks__is_active=True
        )
        pending_licences = ImportApplication.objects.filter(
            tasks__task_type=Task.TaskType.CHIEF_WAIT, tasks__is_active=True
        )

        context = {
            "failed_batches_count": 0,
            "failed_batches": [],
            "failed_licences_count": failed_licences.count(),
            "failed_licences": failed_licences,
            "pending_batches_count": 0,
            "pending_batches": [],
            "pending_licences_count": pending_licences.count(),
            "pending_licences": pending_licences,
        }

        return super().get_context_data(**kwargs) | context


class PendingBatches(_BaseTemplateView):
    template_name = "web/domains/chief/pending_batches.html"


class FailedBatches(_BaseTemplateView):
    template_name = "web/domains/chief/failed_batches.html"


class PendingLicences(_BaseTemplateView):
    template_name = "web/domains/chief/pending_licences.html"


class FailedLicences(_BaseTemplateView):
    template_name = "web/domains/chief/failed_licences.html"
