import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from web.flow.models import Task
from web.notify import notify

from . import forms
from .models import AccessRequest, ExporterAccessRequest, ImporterAccessRequest

logger = logging.get_logger(__name__)


@login_required
def importer_access_request(request):
    with transaction.atomic():
        if request.POST:
            form = forms.ImporterAccessRequestForm(data=request.POST)
            if form.is_valid():
                application = form.save(commit=False)
                application.submitted_by = request.user
                application.last_update_by = request.user
                application.process_type = ImporterAccessRequest.PROCESS_TYPE
                application.save()

                notify.access_requested_importer(application.pk)
                Task.objects.create(process=application, task_type="request", owner=request.user)

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
def exporter_access_request(request):
    with transaction.atomic():
        form = forms.ExporterAccessRequestForm()
        if request.POST:
            form = forms.ExporterAccessRequestForm(data=request.POST)
            if form.is_valid():
                application = form.save(commit=False)
                application.submitted_by = request.user
                application.last_update_by = request.user
                application.process_type = ExporterAccessRequest.PROCESS_TYPE
                application.save()

                notify.access_requested_exporter(application.pk)
                Task.objects.create(process=application, task_type="request", owner=request.user)

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


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
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

        task = application.get_task(AccessRequest.SUBMITTED, "request")

        if request.POST:
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
            "object": application,
            "task": task,
            "form": form,
        }

    return render(
        request=request, template_name="web/domains/case/access/management.html", context=context
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def management_access_approval(request, pk, entity):
    # FIXME: when removing viewflow form Access Approval
    with transaction.atomic():
        application = get_object_or_404(AccessRequest.objects.select_for_update(), pk=pk)
        try:
            application = application.importeraccessrequest
        except ObjectDoesNotExist:
            application = application.exporteraccessrequest
        task = application.get_task(AccessRequest.SUBMITTED, "request")
        context = {
            "object": application,
            "task": task,
        }

    return render(
        request=request,
        template_name="web/domains/case/access/management-access-approval.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
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

        task = application.get_task(AccessRequest.SUBMITTED, "request")

        if request.POST:
            form = forms.CloseAccessRequestForm(instance=application, data=request.POST)
            if form.is_valid():
                form.save()
                application.status = AccessRequest.CLOSED
                application.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                notify.access_request_closed(application)
                return redirect(reverse("workbasket"))
        else:
            form = forms.CloseAccessRequestForm(instance=application)

        context = {"object": application, "task": task, "form": form}

    return render(
        request=request,
        template_name="web/domains/case/access/management-response.html",
        context=context,
    )


class AccessRequestCreatedView(TemplateView):
    template_name = "web/domains/case/access/request-access-success.html"
