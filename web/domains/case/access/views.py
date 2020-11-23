import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from web.domains.case.fir.forms import (
    FurtherInformationRequestForm,
    FurtherInformationRequestResponseForm,
)
from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.file.views import handle_uploaded_file
from web.domains.template.models import Template
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
def case_view(request, application_pk, entity):
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        application.get_task(AccessRequest.SUBMITTED, "request")

    context = {"object": application}
    return render(request, "web/domains/case/access/case-view.html", context)


@login_required
def case_firs(request, application_pk, entity):
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        application.get_task(AccessRequest.SUBMITTED, "request")

    context = {
        "object": application,
        "firs": application.further_information_requests.filter(
            Q(status=FurtherInformationRequest.OPEN)
            | Q(status=FurtherInformationRequest.RESPONDED)
            | Q(status=FurtherInformationRequest.CLOSED)
        ),
        "entity": entity,
    }
    return render(request, "web/domains/case/access/case-firs.html", context)


@login_required
def case_fir_respond(request, application_pk, entity, fir_pk):
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        fir = get_object_or_404(application.further_information_requests.open(), pk=fir_pk)

        application.get_task(AccessRequest.SUBMITTED, "request")
        fir_task = fir.get_task(FurtherInformationRequest.OPEN, "notify_contacts")

        if request.POST:
            form = FurtherInformationRequestResponseForm(instance=fir, data=request.POST)
            files = request.FILES.getlist("files")
            if form.is_valid():
                fir = form.save()
                for f in files:
                    handle_uploaded_file(f, request.user, fir.files)

                fir.response_datetime = timezone.now()
                fir.status = FurtherInformationRequest.RESPONDED
                fir.response_by = request.user
                fir.save()

                fir_task.is_active = False
                fir_task.finished = timezone.now()
                fir_task.save()

                Task.objects.create(process=fir, task_type="responded", owner=request.user)

                notify.further_information_request_access_request_responded(fir)

                return redirect(reverse("workbasket"))
        else:
            form = FurtherInformationRequestResponseForm(instance=fir)

    context = {"object": application, "fir": fir, "form": form}
    return render(request, "web/domains/case/access/case-fir-respond.html", context)


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


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def management_firs(request, application_pk, entity):
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=application_pk
            )

        application.get_task(AccessRequest.SUBMITTED, "request")
        context = {
            "object": application,
            "firs": application.further_information_requests.exclude(
                status=FurtherInformationRequest.DELETED
            ),
            "entity": entity,
        }
    return render(
        request=request,
        template_name="web/domains/case/access/management-firs.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def add_fir(request, application_pk, entity):
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=application_pk
            )

        application.get_task(AccessRequest.SUBMITTED, "request")
        template = Template.objects.get(template_code="IAR_RFI_EMAIL", is_active=True)
        # TODO: use case reference
        title_mapping = {"REQUEST_REFERENCE": application.pk}
        content_mapping = {
            "REQUESTER_NAME": application.submitted_by,
            "CURRENT_USER_NAME": request.user,
            "REQUEST_REFERENCE": application.pk,
        }
        fir = application.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by=request.user,
            request_subject=template.get_title(title_mapping),
            request_detail=template.get_content(content_mapping),
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )

        Task.objects.create(process=fir, task_type="check_draft", owner=request.user)

    return redirect(
        reverse(
            "access:case-management-firs",
            kwargs={"application_pk": application_pk, "entity": entity},
        )
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_fir(request, application_pk, entity, fir_pk):
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=application_pk
            )

        fir = get_object_or_404(application.further_information_requests.draft(), pk=fir_pk)

        application.get_task(AccessRequest.SUBMITTED, "request")
        fir_task = fir.get_task(FurtherInformationRequest.DRAFT, "check_draft")

        if request.POST:
            form = FurtherInformationRequestForm(request.POST, instance=fir)
            files = request.FILES.getlist("files")
            if form.is_valid():
                fir = form.save()
                for f in files:
                    handle_uploaded_file(f, request.user, fir.files)

                if "send" in form.data:
                    fir.status = FurtherInformationRequest.OPEN
                    fir.save()
                    notify.further_information_request_access_request(fir)

                    fir_task.is_active = False
                    fir_task.finished = timezone.now()
                    fir_task.save()

                    Task.objects.create(process=fir, task_type="notify_contacts", previous=fir_task)

                return redirect(
                    reverse(
                        "access:case-management-firs",
                        kwargs={"application_pk": application_pk, "entity": entity,},
                    )
                )
        else:
            form = FurtherInformationRequestForm(instance=fir)

        context = {"object": application, "form": form, "entity": entity, "fir": fir}

    return render(
        request=request,
        template_name="web/domains/case/access/management-edit-fir.html",
        context=context,
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_fir(request, application_pk, entity, fir_pk):
    with transaction.atomic():
        if entity == "importer":
            application = get_object_or_404(
                ImporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        else:
            application = get_object_or_404(
                ExporterAccessRequest.objects.select_for_update(), pk=application_pk
            )
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)

        application.get_task(AccessRequest.SUBMITTED, "request")
        fir_tasks = fir.get_active_tasks()

        fir.is_active = False
        fir.status = FurtherInformationRequest.DELETED
        fir.save()

        fir_tasks.update(is_active=False, finished=timezone.now())

    return redirect(
        reverse(
            "access:case-management-firs",
            kwargs={"application_pk": application_pk, "entity": entity},
        )
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def withdraw_fir(request, application_pk, entity, fir_pk):
    with transaction.atomic():
        application = get_object_or_404(
            AccessRequest.objects.select_for_update(), pk=application_pk
        )
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)

        application.get_task(AccessRequest.SUBMITTED, "request")
        fir_task = fir.get_task(FurtherInformationRequest.OPEN, "notify_contacts")

        fir.status = FurtherInformationRequest.DRAFT
        fir.save()

        fir_task.is_active = False
        fir_task.finished = timezone.now()
        fir_task.save()

        Task.objects.create(process=fir, task_type="check_draft", previous=fir_task)

        application.further_information_requests.filter(pk=fir_pk).update(
            is_active=True, status=FurtherInformationRequest.DRAFT
        )

    return redirect(
        reverse(
            "access:case-management-firs",
            kwargs={"application_pk": application_pk, "entity": entity},
        )
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def close_fir(request, application_pk, entity, fir_pk):
    with transaction.atomic():
        application = get_object_or_404(
            AccessRequest.objects.select_for_update(), pk=application_pk
        )
        fir = get_object_or_404(application.further_information_requests.active(), pk=fir_pk)
        try:
            fir_task = fir.get_task(FurtherInformationRequest.OPEN, "notify_contacts")
        except Exception:
            fir_task = fir.get_task(FurtherInformationRequest.RESPONDED, "responded")

        fir.status = FurtherInformationRequest.CLOSED
        fir.save()

        fir_task.is_active = False
        fir_task.finished = timezone.now()
        fir_task.save()

        application.get_task(AccessRequest.SUBMITTED, "request")
        application.further_information_requests.filter(pk=fir_pk).update(
            is_active=False, status=FurtherInformationRequest.CLOSED
        )

    return redirect(
        reverse(
            "access:case-management-firs",
            kwargs={"application_pk": application_pk, "entity": entity},
        )
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def fir_archive_file(request, application_pk, entity, fir_pk, file_pk):
    with transaction.atomic():
        application = get_object_or_404(
            AccessRequest.objects.select_for_update(), pk=application_pk
        )
        application.get_task(AccessRequest.SUBMITTED, "request")
        document = application.further_information_requests.get(pk=fir_pk).files.get(pk=file_pk)
        document.is_active = False
        document.save()

    return redirect(
        reverse(
            "access:case-management-firs-edit",
            kwargs={"application_pk": application_pk, "entity": entity, "fir_pk": fir_pk},
        )
    )
