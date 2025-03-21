from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.generic.detail import DetailView
from storages.backends.s3boto3 import S3Boto3StorageFile

from web.domains.case._import.fa.forms import ImportContactKnowBoughtFromForm
from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import SubmitForm
from web.domains.case.services import case_progress
from web.domains.case.utils import (
    get_application_form,
    redirect_after_submit,
    submit_application,
    view_application_file,
)
from web.domains.case.views.utils import get_caseworker_view_readonly_status
from web.domains.file.utils import create_file_model
from web.domains.template.utils import add_template_data_on_submit
from web.models import File, Task, User
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .forms import (
    AddDFLGoodsCertificateForm,
    DFLChecklistForm,
    DFLChecklistOptionalForm,
    DFLSupplementaryReportFirearmForm,
    DFLSupplementaryReportUploadFirearmForm,
    EditDFLGoodsCertificateDescriptionForm,
    EditDFLGoodsCertificateForm,
    EditFaDFLForm,
    SubmitFaDFLForm,
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


def check_can_edit_application(user: User, application: DFLApplication) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


@login_required
def edit_dfl(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        form = get_application_form(application, request, EditFaDFLForm, SubmitFaDFLForm)

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("import:fa-dfl:edit", kwargs={"application_pk": application_pk})
                )

        context = {
            "process": application,
            "form": form,
            "page_title": _get_page_title("Edit"),
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/fa-dfl/edit.html", context)


class DFLGoodsCertificateDetailView(
    LoginRequiredMixin, case_progress.InProgressApplicationStatusTaskMixin, DetailView
):
    http_method_names = ["get"]
    template_name = "web/domains/case/import/fa-dfl/goods-list.html"

    # Extra typing for clarity
    application: DFLApplication

    def has_object_permission(self) -> bool:
        """Handles all permission checking required to prove a request user can access this view."""
        check_can_edit_application(self.request.user, self.application)

        return True

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        goods_list = (
            self.application.goods_certificates.filter(is_active=True)
            .select_related("issuing_country")
            .order_by("pk")
        )

        return context | {
            "case_type": "import",
            "process": self.application,
            "page_title": _get_page_title("Goods Certificates"),
            "goods_list": goods_list,
        }


@login_required
def add_goods_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = AddDFLGoodsCertificateForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document: S3Boto3StorageFile = form.cleaned_data.get("document")
                extra_args = {
                    field: value
                    for (field, value) in form.cleaned_data.items()
                    if field not in ["document"]
                }
                extra_args["goods_description_original"] = form.cleaned_data["goods_description"]

                create_file_model(
                    document,
                    request.user,
                    application.goods_certificates,
                    extra_args=extra_args,
                )

                return redirect(
                    reverse("import:fa-dfl:list-goods", kwargs={"application_pk": application_pk})
                )
        else:
            form = AddDFLGoodsCertificateForm()

        context = {
            "process": application,
            "form": form,
            "page_title": _get_page_title("Add Goods Certificate"),
            "case_type": "import",
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
        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        document = application.goods_certificates.filter(is_active=True).get(pk=document_pk)

        if request.method == "POST":
            form = EditDFLGoodsCertificateForm(data=request.POST, instance=document)

            if form.is_valid():
                goods_cert = form.save(commit=False)
                goods_cert.goods_description_original = goods_cert.goods_description
                goods_cert.save()

                return redirect(
                    reverse("import:fa-dfl:list-goods", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditDFLGoodsCertificateForm(instance=document)

        context = {
            "process": application,
            "form": form,
            "page_title": _get_page_title("Edit Goods Certificate"),
            "case_type": "import",
        }

        return render(
            request, "web/domains/case/import/fa-dfl/edit_goods_certificate.html", context
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_goods_certificate_description(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    """Admin only view accessed via the response preparation screen"""

    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        document = application.goods_certificates.filter(is_active=True).get(pk=document_pk)

        if request.method == "POST":
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
            "form": form,
            "case_type": "import",
            "page_title": _get_page_title("Edit Goods Certificate"),
        }

        return render(
            request,
            "web/domains/case/import/manage/response-prep-edit-form.html",
            context,
        )


@login_required
@require_POST
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def reset_goods_certificate_description(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        goods = get_object_or_404(application.goods_certificates, pk=document_pk)
        goods.goods_description = goods.goods_description_original
        goods.save()

        return redirect(
            reverse(
                "case:prepare-response",
                kwargs={"application_pk": application.pk, "case_type": "import"},
            )
        )


@require_GET
@login_required
def view_goods_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: DFLApplication = get_object_or_404(DFLApplication, pk=application_pk)

    # Permission checks in view_application_file
    return view_application_file(
        request.user,
        application,
        application.goods_certificates.filter(is_active=True),
        document_pk,
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
        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        document = application.goods_certificates.filter(is_active=True).get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(
            reverse("import:fa-dfl:list-goods", kwargs={"application_pk": application_pk})
        )


@login_required
def submit_dfl(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = _get_dfl_errors(application)

        if request.method == "POST":
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                submit_application(application, request, task)
                add_template_data_on_submit(application)

                # Only create if needed
                # This view gets called when an applicant submits changes
                DFLSupplementaryInfo.objects.get_or_create(import_application=application)

                return redirect_after_submit(application)

        else:
            form = SubmitForm()

        context = {
            "process": application,
            "page_title": _get_page_title("Submit Application"),
            "form": form,
            "declaration": application.application_type.declaration_template,
            "errors": errors if errors.has_errors() else None,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/import-case-submit.html", context)


def _get_dfl_errors(application: DFLApplication) -> ApplicationErrors:
    errors = ApplicationErrors()

    edit_url = reverse("import:fa-dfl:edit", kwargs={"application_pk": application.pk})
    edit_url = f"{edit_url}?validate"
    add_goods_url = reverse("import:fa-dfl:add-goods", kwargs={"application_pk": application.pk})

    # Check main form
    application_details_errors = PageErrors(page_name="Application Details", url=edit_url)
    application_form = SubmitFaDFLForm(data=model_to_dict(application), instance=application)
    create_page_errors(application_form, application_details_errors)
    errors.add(application_details_errors)

    # Check goods certificates
    if not application.goods_certificates.filter(is_active=True).exists():
        goods_errors = PageErrors(
            page_name="Application Details - Goods Certificates", url=add_goods_url
        )
        goods_errors.add(
            FieldError(
                field_name="Goods Certificate", messages=["At least one certificate must be added"]
            )
        )
        errors.add(goods_errors)

    # Check know bought from
    bought_from_errors = PageErrors(
        page_name="Application Details - Details of Who Bought From",
        url=reverse("import:fa:manage-import-contacts", kwargs={"application_pk": application.pk}),
    )

    kbf_form = ImportContactKnowBoughtFromForm(
        data={"know_bought_from": application.know_bought_from}, application=application
    )
    create_page_errors(kbf_form, bought_from_errors)

    if application.know_bought_from and not application.importcontact_set.exists():
        bought_from_errors.add(
            FieldError(field_name="Person", messages=["At least one person must be added"])
        )

    errors.add(bought_from_errors)

    errors.add(get_org_update_request_errors(application, "import"))

    return errors


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DFLApplication = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )
        readonly_view = get_caseworker_view_readonly_status(application, "import", request.user)
        checklist, created = DFLChecklist.objects.get_or_create(import_application=application)

        if request.method == "POST" and not readonly_view:
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
                form = DFLChecklistForm(instance=checklist, readonly_form=readonly_view)
            else:
                form = DFLChecklistForm(
                    data=model_to_dict(checklist), instance=checklist, readonly_form=readonly_view
                )

        context = {
            "process": application,
            "page_title": _get_page_title("Checklist"),
            "form": form,
            "readonly_view": readonly_view,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/checklist.html",
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
        check_can_edit_application(request.user, application)
        case_progress.application_is_complete(application)

        supplementary_info: DFLSupplementaryInfo = application.supplementary_info
        report: DFLSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
        goods_certificate: DFLGoodsCertificate = application.goods_certificates.filter(
            is_active=True
        ).get(pk=goods_pk)

        if request.method == "POST":
            form = DFLSupplementaryReportFirearmForm(data=request.POST)

            if form.is_valid():
                report_firearm: DFLSupplementaryReportFirearm = form.save(commit=False)
                report_firearm.report = report
                report_firearm.is_manual = True
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
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Add Firearm Details",
            "form": form,
            "report": report,
            "goods_description": goods_certificate.goods_description,
        }

        template = "web/domains/case/import/fa/provide-report/edit-report-firearm-manual.html"

        return render(request=request, template_name=template, context=context)


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

        check_can_edit_application(request.user, application)
        case_progress.application_is_complete(application)
        supplementary_info: DFLSupplementaryInfo = application.supplementary_info
        report: DFLSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
        report_firearm: DFLSupplementaryReportFirearm = report.firearms.get(pk=report_firearm_pk)

        if request.method == "POST":
            form = DFLSupplementaryReportFirearmForm(data=request.POST, instance=report_firearm)

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
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Edit Firearm Details",
            "form": form,
            "report": report,
            "goods_description": report_firearm.get_description(),
        }

        template = "web/domains/case/import/fa/provide-report/edit-report-firearm-manual.html"

        return render(request=request, template_name=template, context=context)


@login_required
def add_report_firearm_upload(
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

        check_can_edit_application(request.user, application)
        case_progress.application_is_complete(application)

        supplementary_info: DFLSupplementaryInfo = application.supplementary_info
        report: DFLSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
        goods_certificate: DFLGoodsCertificate = application.goods_certificates.filter(
            is_active=True
        ).get(pk=goods_pk)

        if request.method == "POST":
            form = DFLSupplementaryReportUploadFirearmForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data["file"]

                report_firearm: DFLSupplementaryReportFirearm = form.save(commit=False)
                report_firearm.report = report
                report_firearm.goods_certificate = goods_certificate
                report_firearm.is_upload = True

                file_model = create_file_model(document, request.user, File.objects)
                report_firearm.document = file_model
                report_firearm.save()

                return redirect(
                    reverse(
                        "import:fa:edit-report",
                        kwargs={"application_pk": application.pk, "report_pk": report.pk},
                    )
                )

        else:
            form = DFLSupplementaryReportUploadFirearmForm()

        context = {
            "process": application,
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Add Firearm Details",
            "form": form,
            "report": report,
            "goods_description": goods_certificate.goods_description,
        }

        template = "web/domains/case/import/fa/provide-report/add-report-firearm-upload.html"

        return render(request=request, template_name=template, context=context)


@require_GET
@login_required
def view_upload_document(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    report_pk: int,
    report_firearm_pk: int,
) -> HttpResponse:
    application: DFLApplication = get_object_or_404(DFLApplication, pk=application_pk)
    supplementary_info: DFLSupplementaryInfo = application.supplementary_info
    report: DFLSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
    report_firearm: DFLSupplementaryReportFirearm = report.firearms.get(pk=report_firearm_pk)
    document = report_firearm.document

    return view_application_file(request.user, application, File.objects, document.pk)


@login_required
@require_POST
def add_report_firearm_no_firearm(
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

        check_can_edit_application(request.user, application)
        case_progress.application_is_complete(application)

        supplementary_info: DFLSupplementaryInfo = application.supplementary_info
        report: DFLSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
        goods_certificate: DFLGoodsCertificate = application.goods_certificates.filter(
            is_active=True
        ).get(pk=goods_pk)

        DFLSupplementaryReportFirearm.objects.create(
            report=report, goods_certificate=goods_certificate, is_no_firearm=True
        )

        return redirect(
            reverse(
                "import:fa:edit-report",
                kwargs={"application_pk": application.pk, "report_pk": report.pk},
            )
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

        check_can_edit_application(request.user, application)
        case_progress.application_is_complete(application)

        supplementary_info: DFLSupplementaryInfo = application.supplementary_info
        report: DFLSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
        report_firearm: DFLSupplementaryReportFirearm = report.firearms.get(pk=report_firearm_pk)

        if report_firearm.is_upload:
            document = report_firearm.document
            report_firearm.document = None

            document.delete()

        report_firearm.delete()

        return redirect(
            reverse(
                "import:fa:edit-report",
                kwargs={"application_pk": application.pk, "report_pk": report.pk},
            )
        )
