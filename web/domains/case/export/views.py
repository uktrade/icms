from typing import NamedTuple, Type

import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from web.domains.case.forms import CloseCaseForm
from web.domains.template.models import Template
from web.flow.models import Task
from web.notify.email import send_email
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .forms import (
    CreateExportApplicationForm,
    PrepareCertManufactureForm,
    SubmitCertManufactureForm,
)
from .models import (
    CertificateOfManufactureApplication,
    ExportApplication,
    ExportApplicationType,
)

logger = logging.get_logger(__name__)

export_case_officer_permission = "web.export_case_officer"


class ExportApplicationChoiceView(PermissionRequiredMixin, TemplateView):
    template_name = "web/domains/case/export/choose.html"
    permission_required = "web.exporter_access"


class CreateExportApplicationConfig(NamedTuple):
    model_class: Type[ExportApplication]
    form_class: Type[CreateExportApplicationForm]
    redirect_view: str
    certificate_message: str


@login_required
@permission_required("web.exporter_access", raise_exception=True)
def create_export_application(request: HttpRequest, *, type_code: str) -> HttpResponse:
    application_type: ExportApplicationType = ExportApplicationType.objects.get(type_code=type_code)

    config = _get_export_app_config(type_code)

    if request.POST:
        form = config.form_class(request.POST, user=request.user)

        if form.is_valid():
            application = config.model_class()
            application.exporter = form.cleaned_data["exporter"]
            application.exporter_office = form.cleaned_data["exporter_office"]
            application.process_type = config.model_class.PROCESS_TYPE
            application.created_by = request.user
            application.last_updated_by = request.user
            application.submitted_by = request.user
            application.application_type = application_type

            with transaction.atomic():
                application.save()
                Task.objects.create(process=application, task_type="prepare", owner=request.user)

            return redirect(reverse(config.redirect_view, kwargs={"pk": application.pk}))
    else:
        form = config.form_class(user=request.user)

    context = {
        "form": form,
        "export_application_type": application_type,
        "certificate_message": config.certificate_message,
    }

    return render(request, "web/domains/case/export/create.html", context)


def _get_export_app_config(type_code: str) -> CreateExportApplicationConfig:
    if type_code == ExportApplicationType.Types.MANUFACTURE:
        return CreateExportApplicationConfig(
            model_class=CertificateOfManufactureApplication,
            form_class=CreateExportApplicationForm,
            redirect_view="export:com-edit",
            certificate_message=(
                "Certificates of Manufacture are applicable only to pesticides that are for export"
                " only and not on free sale on the domestic market."
            ),
        )

    # cfs message to add when supporting Certificate of Free Sale application type
    # cfs_cert_message = (
    #     "If you are supplying the product to a client in the UK/EU then you do not require a certificate."
    #     " Your client will need to apply for a certificate if they subsequently export it to one of their"
    #     " clients outside of the EU."
    # )

    raise NotImplementedError(f"type_code not supported: {type_code}")


@login_required
@permission_required("web.exporter_access", raise_exception=True)
def edit_com(request, pk):
    with transaction.atomic():
        appl = get_object_or_404(
            CertificateOfManufactureApplication.objects.select_for_update(), pk=pk
        )

        task = appl.get_task(ExportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_exporter", appl.exporter):
            raise PermissionDenied

        if request.POST:
            form = PrepareCertManufactureForm(data=request.POST, instance=appl)

            if form.is_valid():
                form.save()

                return redirect(reverse("export:com-edit", kwargs={"pk": pk}))

        else:
            form = PrepareCertManufactureForm(instance=appl, initial={"contact": request.user})

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": appl,
            "task": task,
            "form": form,
        }

        return render(request, "web/domains/case/export/prepare-com.html", context)


@login_required
@permission_required("web.exporter_access", raise_exception=True)
def submit_com(request, pk):
    with transaction.atomic():
        appl = get_object_or_404(
            CertificateOfManufactureApplication.objects.select_for_update(), pk=pk
        )

        task = appl.get_task(ExportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_exporter", appl.exporter):
            raise PermissionDenied

        errors = ApplicationErrors()
        page_errors = PageErrors(
            page_name="Application details", url=reverse("export:com-edit", kwargs={"pk": pk})
        )
        create_page_errors(
            PrepareCertManufactureForm(data=model_to_dict(appl), instance=appl), page_errors
        )
        errors.add(page_errors)

        if request.POST:
            form = SubmitCertManufactureForm(data=request.POST)
            go_back_to_edit = "_edit_application" in request.POST

            if go_back_to_edit:
                return redirect(reverse("export:com-edit", kwargs={"pk": pk}))

            if form.is_valid() and not errors.has_errors():
                appl.status = ExportApplication.SUBMITTED
                appl.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                # TODO: set owner when case processing workflow is done
                Task.objects.create(process=appl, task_type="process", previous=task)

                return redirect(reverse("home"))

        else:
            form = SubmitCertManufactureForm()

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": appl,
            "task": task,
            "exporter_name": appl.exporter.name,
            "form": form,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/export/submit-com.html", context)


@login_required
@permission_required(export_case_officer_permission, raise_exception=True)
@require_POST
def take_ownership(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ExportApplication.objects.select_for_update(), pk=pk)
        application.get_task(ExportApplication.SUBMITTED, "process")
        application.case_owner = request.user
        application.save()

    return redirect(reverse("workbasket"))


@login_required
@permission_required(export_case_officer_permission, raise_exception=True)
@require_POST
def release_ownership(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ExportApplication.objects.select_for_update(), pk=pk)
        application.get_task(ExportApplication.SUBMITTED, "process")
        application.case_owner = None
        application.save()

    return redirect(reverse("workbasket"))


@login_required
@permission_required(export_case_officer_permission, raise_exception=True)
def management(request, pk):
    with transaction.atomic():
        application = get_object_or_404(ExportApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(ExportApplication.SUBMITTED, "process")
        form = CloseCaseForm()

        context = {
            "case_type": "export",
            "process": application,
            "task": task,
            "form": form,
        }
        if request.POST:
            application.status = ExportApplication.STOPPED
            application.save()

            task.is_active = False
            task.finished = timezone.now()
            task.save()

            if request.POST.get("send_email"):
                template = Template.objects.get(template_code="STOP_CASE")
                subject = template.get_title({"CASE_REFERENCE": application.pk})
                body = template.get_content({"CASE_REFERENCE": application.pk})
                recipients = [application.contact.email]
                recipients.extend(
                    application.exporter.baseteam_ptr.members.values_list("email", flat=True)
                )
                recipients = set(recipients)
                send_email(subject, body, recipients)

            return redirect(reverse("workbasket"))

    return render(
        request=request, template_name="web/domains/case/export/management.html", context=context
    )
