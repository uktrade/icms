from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Window
from django.db.models.functions import RowNumber
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin

from web.domains.case.forms import (
    VariationRequestCancelForm,
    VariationRequestExportCancelForm,
    VariationRequestForm,
)
from web.domains.case.services import document_pack, reference
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.mail.constants import EmailTypes
from web.mail.emails import send_variation_request_email
from web.models import Process, Task, VariationRequest
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest

from .mixins import ApplicationAndTaskRelatedObjectMixin
from .utils import get_caseworker_view_readonly_status


class VariationRequestManageView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """ILB Case management view for viewing application variations."""

    # PermissionRequiredMixin config
    permission_required = [Perms.sys.ilb_admin]

    # DetailView config
    model = Process
    pk_url_kwarg = "application_pk"

    def get_context_data(self, **kwargs):
        application = self.object.get_specific_model()
        case_type = self.kwargs["case_type"]

        readonly_view = get_caseworker_view_readonly_status(
            application, case_type, self.request.user
        )

        context = super().get_context_data(**kwargs)

        variation_requests = application.variation_requests.order_by(
            "-requested_datetime"
        ).annotate(vr_num=Window(expression=RowNumber()))

        return context | {
            "page_title": f"Variations {application.get_reference()}",
            "process": application,
            "case_type": case_type,
            "readonly_view": readonly_view,
            "variation_requests": variation_requests,
        }

    def get_template_names(self) -> list[str]:
        case_type = self.kwargs["case_type"]

        if case_type == "import":
            return ["web/domains/case/manage/variations/import/manage.html"]

        if case_type == "export":
            return ["web/domains/case/manage/variations/export/manage.html"]

        raise NotImplementedError(f"Unknown case_type {case_type}")


@method_decorator(transaction.atomic, name="post")
class VariationRequestCancelView(
    LoginRequiredMixin, PermissionRequiredMixin, ApplicationAndTaskRelatedObjectMixin, UpdateView
):
    """ILB Case management view for cancelling a request variation.

    Used by both Import & Export applications
    Import applications require a "reject_cancellation_reason"
    Export applications simply call the endpoint with no form data.
    This is called when the variation was raised in error.
    """

    # ApplicationAndTaskRelatedObjectMixin
    current_status = [ImpExpStatus.VARIATION_REQUESTED]
    current_task_type = Task.TaskType.PROCESS

    next_status = ImpExpStatus.COMPLETED
    next_task_type = None

    # PermissionRequiredMixin config
    permission_required = [Perms.sys.ilb_admin]

    # UpdateView config
    success_url = reverse_lazy("workbasket")
    pk_url_kwarg = "variation_request_pk"
    model = VariationRequest

    # Note: Only used for import applications
    template_name = "web/domains/case/manage/variations-cancel.html"

    # Extra typing for clarity
    object: VariationRequest
    application: ImpOrExp
    task: Task

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "page_title": f"Variations {self.application.get_reference()}",
            "case_type": self.kwargs["case_type"],
            "process": self.application,
            "vr_num": self.application.variation_requests.count(),
        }

    def get_form_class(self):
        if self.application.is_import_application():
            return VariationRequestCancelForm

        return VariationRequestExportCancelForm

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        result = super().form_valid(form)

        # Having saved the cancellation reason we need to do a few things
        self.object.refresh_from_db()
        self.object.status = VariationRequest.Statuses.CANCELLED
        self.object.closed_datetime = timezone.now()
        self.object.closed_by = self.request.user
        self.object.save()

        # Export applications need the reference updating
        if not self.application.is_import_application():
            self.application.reference = reference.get_variation_request_case_reference(
                self.application
            )

        # Cancel the draft licence/Certificate
        document_pack.pack_draft_archive(self.application)
        self.application.update_order_datetime()
        self.update_application_status()
        self.update_application_tasks()
        send_variation_request_email(
            self.object, EmailTypes.APPLICATION_VARIATION_REQUEST_CANCELLED, self.application
        )
        return result


@method_decorator(transaction.atomic, name="post")
class VariationRequestRequestUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, ApplicationAndTaskRelatedObjectMixin, UpdateView
):
    """ILB Case management view for requesting an update from the applicant."""

    # ApplicationAndTaskRelatedObjectMixin Config
    current_status = [ImpExpStatus.VARIATION_REQUESTED]
    current_task_type = None  # We will not be updating any existing tasks
    next_status = None  # We will not be updating the status
    next_task_type = Task.TaskType.VR_REQUEST_CHANGE

    # PermissionRequiredMixin
    permission_required = [Perms.sys.ilb_admin]

    # UpdateView config
    pk_url_kwarg = "variation_request_pk"
    model = VariationRequest
    fields = ["update_request_reason"]
    template_name = "web/domains/case/manage/variations-request-update.html"

    # Extra typing for clarity
    object: VariationRequest

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "page_title": f"Variations {self.application.get_reference()}",
            "case_type": self.kwargs["case_type"],
            "process": self.application,
            "vr_num": self.application.variation_requests.count(),
        }

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        result = super().form_valid(form)
        self.application.update_order_datetime()
        self.application.save()
        self.update_application_tasks()
        send_variation_request_email(
            self.object, EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED, self.application
        )
        return result

    def get_success_url(self):
        return reverse(
            "case:variation-request-manage",
            kwargs={"application_pk": self.application.pk, "case_type": self.kwargs["case_type"]},
        )


@method_decorator(transaction.atomic, name="post")
class VariationRequestCancelUpdateRequestView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ApplicationAndTaskRelatedObjectMixin,
    SingleObjectMixin,
    View,
):
    """View to allow ILB admin to cancel the variation request update from the applicant."""

    # ApplicationAndTaskRelatedObjectMixin
    current_status = [ImpExpStatus.VARIATION_REQUESTED]
    current_task_type = Task.TaskType.VR_REQUEST_CHANGE

    # SingleObjectMixin
    model = VariationRequest
    pk_url_kwarg = "variation_request_pk"

    # PermissionRequiredMixin
    permission_required = [Perms.sys.ilb_admin]

    # View
    http_method_names = ["post"]

    # Extra typing for clarity
    object: VariationRequest

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        variation_request = self.get_object()
        self.set_application_and_task()

        # Reset the update request reason
        variation_request.update_request_reason = None
        variation_request.save()

        # Close the task
        self.update_application_tasks()
        send_variation_request_email(
            variation_request,
            EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_CANCELLED,
            self.application,
        )

        return redirect(
            "case:variation-request-manage",
            application_pk=self.application.pk,
            case_type=self.kwargs["case_type"],
        )


@method_decorator(transaction.atomic, name="post")
class VariationRequestRespondToUpdateRequestView(
    LoginRequiredMixin, PermissionRequiredMixin, ApplicationAndTaskRelatedObjectMixin, UpdateView
):
    """View used by applicant to update a variation request."""

    current_status = [ImpExpStatus.VARIATION_REQUESTED]
    current_task_type = Task.TaskType.VR_REQUEST_CHANGE

    # UpdateView config
    model = VariationRequest
    pk_url_kwarg = "variation_request_pk"
    form_class = VariationRequestForm
    success_url = reverse_lazy("workbasket")
    template_name = "web/domains/case/variation-request-update.html"

    # Extra typing for clarity
    object: VariationRequest

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        return context | {
            "page_title": f"Variations {self.application.get_reference()}",
            "case_type": self.kwargs["case_type"],
            "process": self.application,
            "vr_num": self.application.variation_requests.count(),
        }

    def form_valid(self, form: ModelForm) -> HttpResponseRedirect:
        result = super().form_valid(form)

        # Having saved the variation request changes we need to do a few things
        self.object.refresh_from_db()
        self.object.update_request_reason = None
        self.object.save()

        self.update_application_tasks()
        self.application.update_order_datetime()
        self.application.save()
        send_variation_request_email(
            self.object, EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_RECEIVED, self.application
        )
        return result

    def has_permission(self):
        application = Process.objects.get(pk=self.kwargs["application_pk"]).get_specific_model()

        return AppChecker(self.request.user, application).can_vary()
