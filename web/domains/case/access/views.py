from typing import Any, Literal

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, TemplateView
from ratelimit import UNSAFE
from ratelimit.decorators import ratelimit

from web.domains.case.access.filters import (
    ExporterAccessRequestFilter,
    ImporterAccessRequestFilter,
)
from web.domains.case.services import case_progress, reference
from web.flow.models import ProcessTypes
from web.models import (
    AccessRequest,
    ExporterAccessRequest,
    FurtherInformationRequest,
    ImporterAccessRequest,
    Task,
)
from web.notify import notify
from web.permissions import Perms, organisation_add_contact
from web.types import AuthenticatedHttpRequest
from web.views import ModelFilterView

from . import forms


class ListImporterAccessRequest(ModelFilterView):
    template_name = "web/domains/case/access/list-importer.html"
    filterset_class = ImporterAccessRequestFilter
    model = ImporterAccessRequest
    permission_required = Perms.sys.ilb_admin
    page_title = "Search Importer Access Requests"

    class Display:
        fields = [
            "submit_datetime",
            ("submitted_by", "submitted_by_email"),
            "request_type",
            ("organisation_name", "organisation_address", "organisation_registered_number"),
            "link",
            "response",
            "closed_datetime",
        ]
        fields_config = {
            "submit_datetime": {"header": "Requested Date", "date_format": True},
            "submitted_by": {"header": "Requested By"},
            "submitted_by_email": {"header": "Email"},
            "request_type": {"header": "Request Type", "method": "get_request_type_display"},
            "organisation_name": {"header": "Name"},
            "organisation_address": {"header": "Address"},
            "organisation_registered_number": {"header": "Registered Number"},
            "link": {"header": "Linked to Importer"},
            "response": {"header": "Response"},
            "closed_datetime": {"header": "Response Date", "date_format": True},
        }


class ListExporterAccessRequest(ModelFilterView):
    template_name = "web/domains/case/access/list-exporter.html"
    filterset_class = ExporterAccessRequestFilter
    model = ExporterAccessRequest
    permission_required = Perms.sys.ilb_admin
    page_title = "Search Exporter Access Requests"

    class Display:
        fields = [
            "submit_datetime",
            ("submitted_by", "submitted_by_email"),
            "request_type",
            ("organisation_name", "organisation_address", "organisation_registered_number"),
            "link",
            "response",
            "closed_datetime",
        ]
        fields_config = {
            "submit_datetime": {"header": "Requested Date", "date_format": True},
            "submitted_by": {"header": "Requested By"},
            "submitted_by_email": {"header": "Email"},
            "request_type": {"header": "Request Type", "method": "get_request_type_display"},
            "organisation_name": {"header": "Name"},
            "organisation_address": {"header": "Address"},
            "organisation_registered_number": {"header": "Registered Number"},
            "link": {"header": "Linked to Exporter"},
            "response": {"header": "Response"},
            "closed_datetime": {"header": "Response Date", "date_format": True},
        }


@login_required
@ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE)
def importer_access_request(request: AuthenticatedHttpRequest) -> HttpResponse:
    with transaction.atomic():
        if request.method == "POST":
            form = forms.ImporterAccessRequestForm(data=request.POST)

            if form.is_valid():
                access_request: ImporterAccessRequest = form.save(commit=False)
                access_request.reference = reference.get_importer_access_request_reference(
                    request.icms.lock_manager
                )
                access_request.submitted_by = request.user
                access_request.last_updated_by = request.user
                access_request.process_type = ImporterAccessRequest.PROCESS_TYPE
                access_request.save()

                Task.objects.create(
                    process=access_request, task_type=Task.TaskType.PROCESS, owner=request.user
                )

                notify.send_access_requested_email(access_request)

                if request.user.has_perm(Perms.sys.importer_access) or request.user.has_perm(
                    Perms.sys.exporter_access
                ):
                    return redirect(reverse("workbasket"))

                # A new user who is not a member of any importer/exporter
                # is redirected to a different success page
                return redirect(reverse("access:requested"))
        else:
            form = forms.ImporterAccessRequestForm()

        context = _get_access_request_context(request)
        context["form"] = form

    return render(request, "web/domains/case/access/request-importer-access.html", context)


@login_required
@ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE)
def exporter_access_request(request: AuthenticatedHttpRequest) -> HttpResponse:
    with transaction.atomic():
        form = forms.ExporterAccessRequestForm()

        if request.method == "POST":
            form = forms.ExporterAccessRequestForm(data=request.POST)

            if form.is_valid():
                access_request: ExporterAccessRequest = form.save(commit=False)
                access_request.reference = reference.get_exporter_access_request_reference(
                    request.icms.lock_manager
                )
                access_request.submitted_by = request.user
                access_request.last_updated_by = request.user
                access_request.process_type = ExporterAccessRequest.PROCESS_TYPE
                access_request.save()

                Task.objects.create(
                    process=access_request, task_type=Task.TaskType.PROCESS, owner=request.user
                )

                notify.send_access_requested_email(access_request)

                if request.user.has_perm(Perms.sys.importer_access) or request.user.has_perm(
                    Perms.sys.exporter_access
                ):
                    return redirect(reverse("workbasket"))

                # A new user who is not a member of any importer/exporter
                # is redirected to a different success page
                return redirect(reverse("access:requested"))

        context = _get_access_request_context(request)
        context["form"] = form

    return render(request, "web/domains/case/access/request-exporter-access.html", context)


def _get_access_request_context(request: AuthenticatedHttpRequest) -> dict[str, Any]:
    pending_status = [AccessRequest.Statuses.SUBMITTED, AccessRequest.Statuses.FIR_REQUESTED]

    return {
        "pending_importer_access_requests": ImporterAccessRequest.objects.filter(
            submitted_by=request.user, status__in=pending_status
        ),
        "pending_exporter_access_requests": ExporterAccessRequest.objects.filter(
            submitted_by=request.user, status__in=pending_status
        ),
    }


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def link_access_request(
    request: AuthenticatedHttpRequest,
    *,
    access_request_pk: int,
    entity: Literal["importer", "exporter"],
) -> HttpResponse:
    with transaction.atomic():
        if entity == "importer":
            access_request = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=access_request_pk
            )
            form_cls = forms.LinkImporterAccessRequestForm
        else:
            access_request = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=access_request_pk
            )
            form_cls = forms.LinkExporterAccessRequestForm

        case_progress.access_request_in_processing(access_request)

        if request.method == "POST":
            form = form_cls(request.POST, instance=access_request)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "access:link-request",
                        kwargs={"access_request_pk": access_request.pk, "entity": entity},
                    )
                )
        else:
            form = form_cls(instance=access_request)

        context = {
            "case_type": "access",
            "process": access_request,
            "form": form,
            "show_agent_link": access_request.is_agent_request,
        }

    return render(
        request=request, template_name="web/domains/case/access/management.html", context=context
    )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def close_access_request(
    request: AuthenticatedHttpRequest,
    *,
    access_request_pk: int,
    entity: Literal["importer", "exporter"],
) -> HttpResponse:
    with transaction.atomic():
        if entity == "importer":
            access_request = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=access_request_pk
            )
        else:
            access_request = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=access_request_pk
            )

        case_progress.access_request_in_processing(access_request)

        if request.method == "POST":
            task = case_progress.get_expected_task(access_request, Task.TaskType.PROCESS)
            form = forms.CloseAccessRequestForm(request.POST, instance=access_request)

            if form.is_valid():
                access_request = form.save(commit=False)

                access_request.status = AccessRequest.Statuses.CLOSED
                access_request.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                # If approving with a link add the user to the org.
                # An access request can still be approved without linking (Preserving old behaviour)
                if access_request.response == AccessRequest.APPROVED and access_request.link:
                    if access_request.is_agent_request:
                        org = access_request.agent_link
                    else:
                        org = access_request.link

                    organisation_add_contact(org, access_request.submitted_by)

                notify.access_request_closed(access_request)

                return redirect(reverse("workbasket"))
        else:
            form = forms.CloseAccessRequestForm(instance=access_request)

        context = {
            "case_type": "access",
            "process": access_request,
            "form": form,
        }

    return render(
        request=request,
        template_name="web/domains/case/access/close-access-request.html",
        context=context,
    )


class AccessRequestHistoryView(PermissionRequiredMixin, DetailView):
    # DetailView Config
    model = AccessRequest
    pk_url_kwarg = "access_request_pk"
    context_object_name = "access_request"
    http_method_names = ["get"]
    template_name = "web/domains/case/access/access-request-history.html"

    # PermissionRequiredMixin Config
    permission_required = [Perms.sys.ilb_admin]

    def get_object(self, queryset=None) -> ImporterAccessRequest | ExporterAccessRequest:
        obj: AccessRequest = super().get_object(queryset)

        return obj.get_specific_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        access_request = context["access_request"]
        entity = "importer" if access_request.process_type == ProcessTypes.IAR else "exporter"

        return context | {
            "page_title": "Access Request History",
            "firs": access_request.further_information_requests.exclude(
                status=FurtherInformationRequest.DELETED
            ).filter(is_active=True),
            "approval_request": access_request.approval_requests.filter(is_active=True).first(),
            "entity": entity,
        }


class AccessRequestCreatedView(TemplateView):
    template_name = "web/domains/case/access/request-access-success.html"
