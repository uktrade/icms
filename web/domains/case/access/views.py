import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from ratelimit import UNSAFE
from ratelimit.decorators import ratelimit

from web.domains.case.access.filters import (
    ExporterAccessRequestFilter,
    ImporterAccessRequestFilter,
)
from web.domains.case.services import case_progress, reference
from web.flow.models import Task
from web.notify import notify
from web.types import AuthenticatedHttpRequest
from web.views import ModelFilterView

from . import forms
from .models import AccessRequest, ExporterAccessRequest, ImporterAccessRequest

logger = logging.get_logger(__name__)


class ListImporterAccessRequest(ModelFilterView):
    template_name = "web/domains/case/access/list-importer.html"
    filterset_class = ImporterAccessRequestFilter
    model = ImporterAccessRequest
    permission_required = "web.ilb_admin"
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
    permission_required = "web.ilb_admin"
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
                application: ImporterAccessRequest = form.save(commit=False)
                application.reference = reference.get_importer_access_request_reference(
                    request.icms.lock_manager
                )
                application.submitted_by = request.user
                application.last_updated_by = request.user
                application.process_type = ImporterAccessRequest.PROCESS_TYPE
                application.save()

                notify.access_requested_importer(application.pk)
                Task.objects.create(
                    process=application, task_type=Task.TaskType.PROCESS, owner=request.user
                )

                if request.user.is_importer() or request.user.is_exporter():
                    return redirect(reverse("workbasket"))

                # A new user who is not a member of any importer/exporter
                # is redirected to a different success page
                return redirect(reverse("access:requested"))
        else:
            form = forms.ImporterAccessRequestForm()

        context = {
            "form": form,
            "exporter_access_requests": ExporterAccessRequest.objects.filter(
                tasks__owner=request.user
            ),
            "importer_access_requests": ImporterAccessRequest.objects.filter(
                tasks__owner=request.user
            ),
        }

    return render(request, "web/domains/case/access/request-importer-access.html", context)


@login_required
@ratelimit(key="ip", rate="5/m", block=True, method=UNSAFE)
def exporter_access_request(request: AuthenticatedHttpRequest) -> HttpResponse:
    with transaction.atomic():
        form = forms.ExporterAccessRequestForm()

        if request.method == "POST":
            form = forms.ExporterAccessRequestForm(data=request.POST)

            if form.is_valid():
                application: ExporterAccessRequest = form.save(commit=False)
                application.reference = reference.get_exporter_access_request_reference(
                    request.icms.lock_manager
                )
                application.submitted_by = request.user
                application.last_updated_by = request.user
                application.process_type = ExporterAccessRequest.PROCESS_TYPE
                application.save()

                notify.access_requested_exporter(application.pk)
                Task.objects.create(
                    process=application, task_type=Task.TaskType.PROCESS, owner=request.user
                )

                if request.user.is_importer() or request.user.is_exporter():
                    return redirect(reverse("workbasket"))

                # A new user who is not a member of any importer/exporter
                # is redirected to a different success page
                return redirect(reverse("access:requested"))

        context = {
            "form": form,
            "exporter_access_requests": ExporterAccessRequest.objects.filter(
                tasks__owner=request.user
            ),
            "importer_access_requests": ImporterAccessRequest.objects.filter(
                tasks__owner=request.user
            ),
        }

    return render(request, "web/domains/case/access/request-exporter-access.html", context)


@permission_required("web.ilb_admin", raise_exception=True)
def management(request, pk, entity):
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=pk
            )
            Form = forms.LinkImporterAccessRequestForm
            permission_codename = "importer_access"
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=pk
            )
            Form = forms.LinkExporterAccessRequestForm
            permission_codename = "exporter_access"

        case_progress.access_request_in_processing(application)

        if request.method == "POST":
            form = Form(instance=application, data=request.POST)
            if form.is_valid():
                form.save()
                application.submitted_by.user_permissions.add(
                    Permission.objects.get(codename=permission_codename)
                )

                return redirect(
                    reverse(
                        "access:case-management", kwargs={"pk": application.pk, "entity": entity}
                    )
                )
        else:
            form = Form(instance=application)

        context = {
            "case_type": "access",
            "process": application,
            "form": form,
        }

    return render(
        request=request, template_name="web/domains/case/access/management.html", context=context
    )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def management_response(request, pk, entity):
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=pk
            )
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=pk
            )

        case_progress.access_request_in_processing(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PROCESS)

        if request.method == "POST":
            form = forms.CloseAccessRequestForm(instance=application, data=request.POST)
            if form.is_valid():
                form.save()
                application.status = AccessRequest.Statuses.CLOSED
                application.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                notify.access_request_closed(application)
                return redirect(reverse("workbasket"))
        else:
            form = forms.CloseAccessRequestForm(instance=application)

        context = {
            "case_type": "access",
            "process": application,
            "form": form,
        }

    return render(
        request=request,
        template_name="web/domains/case/access/management-response.html",
        context=context,
    )


class AccessRequestCreatedView(TemplateView):
    template_name = "web/domains/case/access/request-access-success.html"
