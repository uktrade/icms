import http
import json
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, TemplateView, View

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.domains.case.tasks import create_case_document_pack
from web.domains.case.views.mixins import ApplicationTaskMixin
from web.models import (
    CaseDocumentReference,
    ICMSHMRCChiefRequest,
    ImportApplication,
    ImportApplicationLicence,
    Task,
)
from web.permissions import Perms
from web.types import AuthenticatedHttpRequest
from web.utils.api.auth import HawkHMRCMixin
from web.utils.sentry import capture_message

from . import client, types, utils


class LicenseDataCallback(HawkHMRCMixin, View):
    """View used by ICMS-HMRC to send licence data back to ICMS."""

    # View Config
    http_method_names = ["post"]

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        licence_replies = types.ChiefLicenceReplyResponseData.model_validate_json(request.body)

        with transaction.atomic():
            for accepted in licence_replies.accepted:
                self.accept_application(accepted)

            for rejected in licence_replies.rejected:
                self.reject_application(rejected)

        return JsonResponse({}, status=http.HTTPStatus.OK)

    def accept_application(self, accepted_licence: types.AcceptedLicence) -> None:
        chief_req = self.get_chief_request(accepted_licence.id)

        utils.chief_licence_reply_approve_licence(chief_req.import_application)
        utils.complete_chief_request(chief_req)

    def reject_application(self, rejected_licence: types.RejectedLicence) -> None:
        chief_req = self.get_chief_request(rejected_licence.id)

        utils.chief_licence_reply_reject_licence(chief_req.import_application)
        utils.fail_chief_request(chief_req, rejected_licence.errors)

    @staticmethod
    def get_chief_request(icms_hmrc_id: str) -> ICMSHMRCChiefRequest:
        chief_req = (
            ICMSHMRCChiefRequest.objects.select_related("import_application")
            .select_for_update()
            .get(icms_hmrc_id=icms_hmrc_id)
        )

        return chief_req


class UsageDataCallbackView(HawkHMRCMixin, View):
    """View used by ICMS-HMRC to send usage data back to ICMS."""

    # View Config
    http_method_names = ["post"]

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        response = types.ChiefUsageDataResponseData.model_validate_json(request.body)

        with transaction.atomic():
            for rec in response.usage_data:
                self._update_import_application_usage_status(rec)

        return JsonResponse({}, status=http.HTTPStatus.OK)

    def _update_import_application_usage_status(self, rec: types.UsageRecord) -> None:
        try:
            licence = ImportApplicationLicence.objects.get(
                status__in=[
                    ImportApplicationLicence.Status.ACTIVE,
                    ImportApplicationLicence.Status.REVOKED,
                ],
                document_references__document_type=CaseDocumentReference.Type.LICENCE,
                document_references__reference=rec.licence_ref,
            )
        except ObjectDoesNotExist:
            capture_message(
                f"licence not found: Unable to set usage status for licence number: {rec.licence_ref}."
            )
            return
        except MultipleObjectsReturned:
            capture_message(
                f"multiple licences found: Unable to set usage status for licence number: {rec.licence_ref}."
            )
            return

        application = licence.import_application
        application.chief_usage_status = rec.licence_status
        application.save()


@method_decorator(transaction.atomic, name="post")
class ResendLicenceToChiefView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ApplicationTaskMixin,
    View,
):
    """View to resend a Licence to CHIEF."""

    # ApplicationTaskMixin
    current_status = [
        ImpExpStatus.VARIATION_REQUESTED,
        ImpExpStatus.PROCESSING,
        ImpExpStatus.REVOKED,
    ]
    current_task_type = Task.TaskType.CHIEF_ERROR

    # Only applies to applications being processed
    next_task_type = Task.TaskType.DOCUMENT_SIGNING

    # PermissionRequiredMixin
    permission_required = [Perms.sys.ilb_admin]

    # View
    http_method_names = ["post"]

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.set_application_and_task()

        if self.application.status == ImpExpStatus.REVOKED:
            client.send_application_to_chief(self.application, self.task, revoke_licence=True)
            messages.success(request, "Revoke licence request send to CHIEF for processing")

        else:
            # Update the current task so `create_case_document_pack` will work correctly
            self.update_application_tasks()

            # Regenerating the licence document pack will send the application to CHIEF
            # after the updated documents have been created.
            create_case_document_pack(self.application, self.request.user)

            messages.success(
                request,
                "Once the licence has been regenerated it will be send to CHIEF for processing",
            )

        return redirect("chief:failed-licences")


@method_decorator(transaction.atomic, name="post")
class RevertLicenceToProcessingView(
    LoginRequiredMixin, PermissionRequiredMixin, ApplicationTaskMixin, View
):
    """View to revert an application with a chief error back to being processed by ILB.

    This can be useful if there is an error in the data and ICMS-HMRC has rejected it.
    """

    # ApplicationTaskMixin
    current_status = [ImpExpStatus.VARIATION_REQUESTED, ImpExpStatus.PROCESSING]
    current_task_type = Task.TaskType.CHIEF_ERROR

    next_task_type = Task.TaskType.PROCESS

    # PermissionRequiredMixin
    permission_required = [Perms.sys.ilb_admin]

    # View
    http_method_names = ["post"]

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.set_application_and_task()

        self.update_application_tasks()
        self.application.update_order_datetime()
        self.application.save()

        messages.success(request, "Licence now back in processing so the error can be corrected.")

        return redirect("chief:failed-licences")


class _BaseTemplateView(PermissionRequiredMixin, TemplateView):
    permission_required = Perms.sys.ilb_admin

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        # We need the counts for each type to show in the navigation tabs.
        failed_licences = ImportApplication.objects.filter(
            tasks__task_type=Task.TaskType.CHIEF_ERROR, tasks__is_active=True
        )
        pending_licences = ImportApplication.objects.filter(
            tasks__task_type__in=[Task.TaskType.CHIEF_WAIT, Task.TaskType.CHIEF_REVOKE_WAIT],
            tasks__is_active=True,
        )

        context = {
            "failed_licences_count": failed_licences.count(),
            "failed_licences": failed_licences,
            "pending_licences_count": pending_licences.count(),
            "pending_licences": pending_licences,
        }

        return super().get_context_data(**kwargs) | context


class PendingLicences(_BaseTemplateView):
    """Licences that have been sent to ICMS-HMRC and therefore CHIEF."""

    template_name = "web/domains/chief/pending_licences.html"


class FailedLicences(_BaseTemplateView):
    """Licences that have failed for reasons that are application specific.

    CHIEF protocol errors (file errors) should be handled in ICMS-HMRC.
    """

    template_name = "web/domains/chief/failed_licences.html"


class ChiefRequestDataView(PermissionRequiredMixin, DetailView):
    permission_required = Perms.sys.ilb_admin
    http_method_names = ["get"]
    pk_url_kwarg = "icmshmrcchiefrequest_id"
    model = ICMSHMRCChiefRequest

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        return JsonResponse(data=self.get_object().request_data)


class CheckChiefProgressView(
    LoginRequiredMixin, PermissionRequiredMixin, ApplicationTaskMixin, View
):
    # View Config
    http_method_names = ["get"]

    # ApplicationTaskMixin Config
    current_status = [
        ImpExpStatus.PROCESSING,
        ImpExpStatus.VARIATION_REQUESTED,
        ImpExpStatus.COMPLETED,
        ImpExpStatus.REVOKED,
    ]

    # PermissionRequiredMixin Config
    permission_required = [Perms.sys.ilb_admin]

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.set_application_and_task()

        active_tasks = case_progress.get_active_task_list(self.application)
        reload_workbasket = False

        if self.application.status == ImpExpStatus.COMPLETED:
            msg = "Accepted - An accepted response has been received from CHIEF."
            reload_workbasket = True

        elif Task.TaskType.CHIEF_ERROR in active_tasks:
            msg = "Rejected - A rejected response has been received from CHIEF."
            reload_workbasket = True

        elif Task.TaskType.CHIEF_WAIT in active_tasks:
            msg = "Awaiting Response - Licence sent to CHIEF, we are awaiting a response"

        elif self.application.status == ImpExpStatus.REVOKED:
            if Task.TaskType.CHIEF_REVOKE_WAIT in active_tasks:
                msg = "Awaiting Response - Licence sent to CHIEF, we are awaiting a response"
            else:
                msg = "Accepted - An accepted response has been received from CHIEF."
                reload_workbasket = True

        else:
            raise Exception("Unknown state for application")

        return JsonResponse(data={"msg": msg, "reload_workbasket": reload_workbasket})


class CheckICMSConnectionView(HawkHMRCMixin, View):
    """View used by ICMS-HMRC to test connection to ICMS"""

    http_method_names = ["post"]

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        data = json.loads(request.body.decode("utf-8"))

        if data != {"foo": "bar"}:
            error_msg = f"Invalid request data: {data}"

            return JsonResponse(status=http.HTTPStatus.BAD_REQUEST, data={"errors": error_msg})

        return JsonResponse(status=http.HTTPStatus.OK, data={"bar": "foo"})
