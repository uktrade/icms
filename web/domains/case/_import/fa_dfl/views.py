from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from storages.backends.s3boto3 import S3Boto3StorageFile

from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import SubmitForm
from web.domains.case.utils import (
    check_application_permission,
    get_application_current_task,
    view_application_file,
)
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .forms import (
    AddDLFGoodsCertificateForm,
    DFLChecklistForm,
    DFLChecklistOptionalForm,
    DFLSupplementaryReportFirearmForm,
    EditDFLGoodsCertificateDescriptionForm,
    EditDLFGoodsCertificateForm,
    PrepareDFLForm,
)
from .models import (
    DFLApplication,
    DFLChecklist,
    DFLGoodsCertificate,
    DFLSupplementaryInfo,
    DFLSupplementaryReport,
    DFLSupplementaryReportFirearm,
)


def _get_page_title(page: str) -> str:
    return f"Firearms and Ammunition (Deactivated Firearms Licence) - {page}"


@login_required
def edit_dfl(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        if request.POST:
            form = PrepareDFLForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()
                return redirect(
                    reverse("import:fa-dfl:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = PrepareDFLForm(instance=application, initial={"contact": request.user})

        goods_list = application.goods_certificates.filter(is_active=True).select_related(
            "issuing_country"
        )

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": _get_page_title("Edit"),
            "goods_list": goods_list,
        }

        return render(request, "web/domains/case/import/fa-dfl/edit.html", context)


@login_required
def add_goods_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "import")
        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        if request.POST:
            form = AddDLFGoodsCertificateForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document: S3Boto3StorageFile = form.cleaned_data.get("document")
                extra_args = {
                    field: value
                    for (field, value) in form.cleaned_data.items()
                    if field not in ["document"]
                }

                create_file_model(
                    document,
                    request.user,
                    application.goods_certificates,
                    extra_args=extra_args,
                )

                return redirect(
                    reverse("import:fa-dfl:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = AddDLFGoodsCertificateForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": _get_page_title("Add Goods Certificate"),
        }

        return render(request, "web/domains/case/import/fa-dfl/add_goods_certificate.html", context)


@login_required
def edit_goods_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        document = application.goods_certificates.get(pk=document_pk)

        if request.POST:
            form = EditDLFGoodsCertificateForm(data=request.POST, instance=document)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:fa-dfl:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditDLFGoodsCertificateForm(instance=document)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": _get_page_title("Edit Goods Certificate"),
        }

        return render(
            request, "web/domains/case/import/fa-dfl/edit_goods_certificate.html", context
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_goods_certificate_description(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    """Admin only view accessed via the response preparation screen"""

    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )

        task = get_application_current_task(application, "import", Task.TaskType.PROCESS)

        document = application.goods_certificates.get(pk=document_pk)

        if request.POST:
            form = EditDFLGoodsCertificateDescriptionForm(data=request.POST, instance=document)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application.pk, "case_type": "import"},
                    )
                )

        else:
            form = EditDFLGoodsCertificateDescriptionForm(instance=document)

        context = {
            "process": application,
            "task": task,
            "form": form,
            "case_type": "import",
            "page_title": _get_page_title("Edit Goods Certificate"),
        }

        return render(
            request,
            "web/domains/case/import/manage/response-prep-edit-form.html",
            context,
        )


@require_GET
@login_required
def view_goods_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: DFLApplication = get_object_or_404(DFLApplication, pk=application_pk)

    return view_application_file(
        request.user, application, application.goods_certificates, document_pk, "import"
    )


@require_POST
@login_required
def delete_goods_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "import")

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        document = application.goods_certificates.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:fa-dfl:edit", kwargs={"application_pk": application_pk}))


@login_required
def submit_dfl(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        errors = _get_dfl_errors(application)

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                application.submit_application(request, task)

                template = Template.objects.get(template_code="COVER_FIREARMS_DEACTIVATED_FIREARMS")
                application.cover_letter = template.get_content(
                    {
                        "CONTACT_NAME": application.contact,
                        "LICENCE_NUMBER": None,  # TODO: What should this be?
                        "APPLICATION_SUBMITTED_DATE": application.submit_datetime,
                        "LICENCE_END_DATE": None,  # TODO: What should this be?
                    }
                )

                application.save()

                DFLSupplementaryInfo.objects.create(import_application=application)

                return application.redirect_after_submit(request)

        else:
            form = SubmitForm()

        declaration = Template.objects.filter(
            is_active=True,
            template_type=Template.DECLARATION,
            application_domain=Template.IMPORT_APPLICATION,
            template_code="IMA_GEN_DECLARATION",
        ).first()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": _get_page_title("Submit Application"),
            "form": form,
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/import/fa-dfl/submit.html", context)


def _get_dfl_errors(application: DFLApplication) -> ApplicationErrors:
    errors = ApplicationErrors()

    edit_url = reverse("import:fa-dfl:edit", kwargs={"application_pk": application.pk})

    # Check main form
    application_details_errors = PageErrors(page_name="Application details", url=edit_url)
    application_form = PrepareDFLForm(data=model_to_dict(application), instance=application)
    create_page_errors(application_form, application_details_errors)
    errors.add(application_details_errors)

    # Check goods certificates
    if not application.goods_certificates.exists():
        goods_errors = PageErrors(page_name="Goods Certificates", url=edit_url)
        goods_errors.add(
            FieldError(
                field_name="Goods Certificate", messages=["At least one certificate must be added"]
            )
        )
        errors.add(goods_errors)

    # Check know bought from
    if application.know_bought_from and not application.importcontact_set.exists():
        page_errors = PageErrors(
            page_name="Details of who bought from",
            url=reverse(
                "import:fa:list-import-contacts", kwargs={"application_pk": application.pk}
            ),
        )

        page_errors.add(
            FieldError(field_name="Person", messages=["At least one person must be added"])
        )

        errors.add(page_errors)

    errors.add(get_org_update_request_errors(application, "import"))

    return errors


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )
        task = get_application_current_task(application, "import", Task.TaskType.PROCESS)
        checklist, created = DFLChecklist.objects.get_or_create(import_application=application)

        if request.POST:
            form: DFLChecklistForm = DFLChecklistOptionalForm(request.POST, instance=checklist)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa-dfl:manage-checklist", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            if created:
                form = DFLChecklistForm(instance=checklist)
            else:
                form = DFLChecklistForm(data=model_to_dict(checklist), instance=checklist)

        context = {
            "process": application,
            "task": task,
            "page_title": _get_page_title("Checklist"),
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )


@login_required
def add_report_firearm_manual(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    report_pk: int,
    goods_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.ACK)

        supplementary_info: DFLSupplementaryInfo = application.supplementary_info
        report: DFLSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
        goods_certificate: DFLGoodsCertificate = application.goods_certificates.get(pk=goods_pk)

        if request.POST:
            form = DFLSupplementaryReportFirearmForm(data=request.POST)

            if form.is_valid():
                report_firearm: DFLSupplementaryReportFirearm = form.save(commit=False)
                report_firearm.report = report
                report_firearm.goods_certificate = goods_certificate
                report_firearm.save()

                return redirect(
                    reverse(
                        "import:fa:edit-report",
                        kwargs={"application_pk": application.pk, "report_pk": report.pk},
                    )
                )

        else:
            form = DFLSupplementaryReportFirearmForm()

        context = {
            "process": application,
            "task": task,
            "process_template": "web/domains/case/import/partials/process.html",
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Add Firearm Details",
            "form": form,
            "report": report,
            "goods_description": goods_certificate.goods_description,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/fa/provide-report/create-report-firearm.html",
            context=context,
        )


@login_required
def edit_report_firearm_manual(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    report_pk: int,
    report_firearm_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.ACK)
        supplementary_info: DFLSupplementaryInfo = application.supplementary_info
        report: DFLSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
        report_firearm: DFLSupplementaryReportFirearm = report.firearms.get(pk=report_firearm_pk)

        if request.POST:
            form = DFLSupplementaryReportFirearmForm(instance=report_firearm, data=request.POST)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa:edit-report",
                        kwargs={"application_pk": application.pk, "report_pk": report.pk},
                    )
                )

        else:
            form = DFLSupplementaryReportFirearmForm(instance=report_firearm)

        context = {
            "process": application,
            "task": task,
            "process_template": "web/domains/case/import/partials/process.html",
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Edit Firearm Details",
            "form": form,
            "report": report,
            "goods_description": report_firearm.get_description(),
        }

        return render(
            request=request,
            template_name="web/domains/case/import/fa/provide-report/create-report-firearm.html",
            context=context,
        )


@login_required
@require_POST
def delete_report_firearm(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    report_pk: int,
    report_firearm_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        get_application_current_task(application, "import", Task.TaskType.ACK)

        supplementary_info: DFLSupplementaryInfo = application.supplementary_info
        report: DFLSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
        report_firearm: DFLSupplementaryReportFirearm = report.firearms.get(pk=report_firearm_pk)
        report_firearm.delete()

        return redirect(
            reverse(
                "import:fa:edit-report",
                kwargs={"application_pk": application.pk, "report_pk": report.pk},
            )
        )
