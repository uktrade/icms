from typing import List, NamedTuple, Type

import structlog as logging
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import TemplateView
from guardian.shortcuts import get_objects_for_user

from web.domains.case.forms import SubmitForm
from web.domains.case.views import check_application_permission
from web.domains.exporter.models import Exporter
from web.domains.user.models import User
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .forms import CreateExportApplicationForm, EditCFSForm, PrepareCertManufactureForm
from .models import (
    CertificateOfFreeSaleApplication,
    CertificateOfManufactureApplication,
    ExportApplication,
    ExportApplicationType,
)

logger = logging.get_logger(__name__)


class ExportApplicationChoiceView(PermissionRequiredMixin, TemplateView):
    template_name = "web/domains/case/export/choose.html"
    permission_required = "web.exporter_access"


class CreateExportApplicationConfig(NamedTuple):
    model_class: Type[ExportApplication]
    form_class: Type[CreateExportApplicationForm]
    certificate_message: str


def _exporters_with_agents(user: User) -> List[int]:
    exporters_with_agents = get_objects_for_user(user, ["web.is_agent_of_exporter"], Exporter)
    return [exporter.pk for exporter in exporters_with_agents]


@login_required
@permission_required("web.exporter_access", raise_exception=True)
def create_export_application(request: AuthenticatedHttpRequest, *, type_code: str) -> HttpResponse:
    application_type: ExportApplicationType = ExportApplicationType.objects.get(type_code=type_code)

    config = _get_export_app_config(type_code)

    if request.POST:
        form = config.form_class(request.POST, user=request.user)

        if form.is_valid():
            application = config.model_class()
            application.exporter = form.cleaned_data["exporter"]
            application.exporter_office = form.cleaned_data["exporter_office"]
            application.agent = form.cleaned_data["agent"]
            application.agent_office = form.cleaned_data["agent_office"]
            application.process_type = config.model_class.PROCESS_TYPE
            application.created_by = request.user
            application.last_updated_by = request.user
            application.submitted_by = request.user
            application.application_type = application_type

            with transaction.atomic():
                application.save()
                Task.objects.create(process=application, task_type="prepare", owner=request.user)

            return redirect(
                reverse(application.get_edit_view_name(), kwargs={"application_pk": application.pk})
            )
    else:
        form = config.form_class(user=request.user)

    context = {
        "form": form,
        "export_application_type": application_type,
        "certificate_message": config.certificate_message,
        "application_title": ExportApplicationType.ProcessTypes(
            config.model_class.PROCESS_TYPE
        ).label,
        "exporters_with_agents": _exporters_with_agents(request.user),
    }

    return render(request, "web/domains/case/export/create.html", context)


def _get_export_app_config(type_code: str) -> CreateExportApplicationConfig:
    if type_code == ExportApplicationType.Types.MANUFACTURE:
        return CreateExportApplicationConfig(
            model_class=CertificateOfManufactureApplication,
            form_class=CreateExportApplicationForm,
            certificate_message=(
                "Certificates of Manufacture are applicable only to pesticides that are for export"
                " only and not on free sale on the domestic market."
            ),
        )

    elif type_code == ExportApplicationType.Types.FREE_SALE:
        return CreateExportApplicationConfig(
            model_class=CertificateOfFreeSaleApplication,
            form_class=CreateExportApplicationForm,
            certificate_message=(
                "If you are supplying the product to a client in the UK/EU then you do not require a certificate."
                " Your client will need to apply for a certificate if they subsequently export it to one of their"
                " clients outside of the EU.\n\n"
                "DIT does not issue Certificates of Free Sale for food, foodsupplements, pesticides and CE marked medical devices."
            ),
        )

    raise NotImplementedError(f"type_code not supported: {type_code}")


@login_required
def edit_com(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        appl: CertificateOfManufactureApplication = get_object_or_404(
            CertificateOfManufactureApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(appl, request.user, "export")

        task = appl.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = PrepareCertManufactureForm(data=request.POST, instance=appl)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("export:com-edit", kwargs={"application_pk": application_pk})
                )

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
def submit_com(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        appl: CertificateOfManufactureApplication = get_object_or_404(
            CertificateOfManufactureApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(appl, request.user, "export")

        task = appl.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        errors = ApplicationErrors()
        page_errors = PageErrors(
            page_name="Application details",
            url=reverse("export:com-edit", kwargs={"application_pk": application_pk}),
        )
        create_page_errors(
            PrepareCertManufactureForm(data=model_to_dict(appl), instance=appl), page_errors
        )
        errors.add(page_errors)

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                appl.submit_application(request, task)

                return appl.redirect_after_submit(request)

        else:
            form = SubmitForm()

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
def edit_cfs(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        appl: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(appl, request.user, "export")

        task = appl.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = EditCFSForm(data=request.POST, instance=appl)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("export:cfs-edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditCFSForm(instance=appl, initial={"contact": request.user})

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": appl,
            "task": task,
            "form": form,
        }

        return render(request, "web/domains/case/export/edit-cfs.html", context)


@login_required
def submit_cfs(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        appl: CertificateOfFreeSaleApplication = get_object_or_404(
            CertificateOfFreeSaleApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(appl, request.user, "export")

        task = appl.get_task(ExportApplication.Statuses.IN_PROGRESS, "prepare")

        errors = ApplicationErrors()
        page_errors = PageErrors(
            page_name="Application details",
            url=reverse("export:cfs-edit", kwargs={"application_pk": application_pk}),
        )
        create_page_errors(EditCFSForm(data=model_to_dict(appl), instance=appl), page_errors)
        errors.add(page_errors)

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                appl.submit_application(request, task)

                return appl.redirect_after_submit(request)

        else:
            form = SubmitForm()

        context = {
            "process_template": "web/domains/case/export/partials/process.html",
            "process": appl,
            "task": task,
            "exporter_name": appl.exporter.name,
            "form": form,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/export/submit-cfs.html", context)
