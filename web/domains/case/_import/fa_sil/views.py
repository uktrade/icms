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
from django.views.generic import DetailView

from web.domains.case import forms as case_forms
from web.domains.case.forms import SubmitForm
from web.domains.case.services import case_progress
from web.domains.case.utils import (
    get_application_form,
    redirect_after_submit,
    submit_application,
    view_application_file,
)
from web.domains.case.views.utils import get_caseworker_view_readonly_status
from web.domains.file.models import File
from web.domains.file.utils import create_file_model
from web.domains.template.utils import (
    add_application_cover_letter,
    add_template_data_on_submit,
)
from web.models import Task, User
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest

from . import forms, models, types
from .utils import (
    _get_report_firearm_form_class,
    _get_report_firearm_model,
    _get_report_upload_firearm_form_class,
    _get_sil_errors,
    _get_sil_section_app_config,
    _get_sil_section_resp_prep_config,
)


def check_can_edit_application(user: User, application: models.SILApplication) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


def check_can_view_application(user: User, application: models.SILApplication) -> None:
    checker = AppChecker(user, application)

    if not checker.can_view():
        raise PermissionDenied


@login_required
def edit(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        form = get_application_form(
            application, request, forms.EditFaSILForm, forms.SubmitFaSILForm
        )

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("import:fa-sil:edit", kwargs={"application_pk": application_pk})
                )
            else:
                messages.error(request, "Failed to save application data, please correct errors.")

        context = {
            "process": application,
            "form": form,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Edit",
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/fa-sil/edit.html", context)


class SILGoodsCertificateDetailView(
    LoginRequiredMixin, case_progress.InProgressApplicationStatusTaskMixin, DetailView
):
    http_method_names = ["get"]
    template_name = "web/domains/case/import/fa-sil/goods/list.html"

    # Extra typing for clarity
    application: models.SILApplication

    def has_object_permission(self) -> bool:
        """Handles all permission checking required to prove a request user can access this view."""
        check_can_edit_application(self.request.user, self.application)

        return True

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        # The goods get loaded directly in the templates so no extra context required.
        return context | {
            "case_type": "import",
            "process": self.application,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Goods",
        }


@login_required
def choose_goods_section(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    application: models.SILApplication = get_object_or_404(models.SILApplication, pk=application_pk)
    check_can_edit_application(request.user, application)

    case_progress.application_in_progress(application)

    has_goods = any(
        getattr(application, s)
        for s in ("section1", "section2", "section5", "section58_obsolete", "section58_other")
    )

    context = {
        "process": application,
        "page_title": "Firearms and Ammunition (Specific Import Licence) - Edit Goods",
        "case_type": "import",
        "has_goods": has_goods,
    }

    return render(request, "web/domains/case/import/fa-sil/choose-goods-section.html", context)


@login_required
def add_section(
    request: AuthenticatedHttpRequest, *, application_pk: int, sil_section_type: str
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        config = _get_sil_section_app_config(sil_section_type)

        if request.method == "POST":
            form = config.form_class(request.POST)

            if form.is_valid():
                goods = form.save(commit=False)
                goods.import_application = application
                goods.description_original = goods.description
                goods.quantity_original = goods.quantity
                goods.save()

                return redirect(
                    reverse("import:fa-sil:list-goods", kwargs={"application_pk": application.pk})
                )
        else:
            form = config.form_class()

        context = {
            "process": application,
            "form": form,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Add Goods",
            "case_type": "import",
        }

        return render(request, config.template, context)


@login_required
def edit_section(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    sil_section_type: str,
    section_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)
        config = _get_sil_section_app_config(sil_section_type)
        goods: types.GoodsModel = get_object_or_404(config.model_class, pk=section_pk)

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = config.form_class(request.POST, instance=goods)
            if form.is_valid():
                goods = form.save(commit=False)
                goods.import_application = application
                goods.description_original = goods.description
                goods.quantity_original = goods.quantity
                goods.save()

                return redirect(
                    reverse("import:fa-sil:list-goods", kwargs={"application_pk": application.pk})
                )

        else:
            form = config.form_class(instance=goods)

        context = {
            "process": application,
            "form": form,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Edit Goods",
            "case_type": "import",
        }

        return render(request, config.template, context)


@login_required
@require_POST
def delete_section(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    sil_section_type: str,
    section_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)
        config = _get_sil_section_app_config(sil_section_type)
        goods: types.GoodsModel = get_object_or_404(config.model_class, pk=section_pk)

        case_progress.application_in_progress(application)

        goods.is_active = False
        goods.save()

        return redirect(
            reverse("import:fa-sil:list-goods", kwargs={"application_pk": application_pk})
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def response_preparation_edit_goods(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    sil_section_type: str,
    section_pk: int,
) -> HttpResponse:
    """Admin only view accessed via the response preparation screen to edit linked goods."""

    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        config = _get_sil_section_resp_prep_config(sil_section_type)
        goods: types.GoodsModel = get_object_or_404(config.model_class, pk=section_pk)

        if request.method == "POST":
            form = config.form_class(request.POST, instance=goods)
            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = config.form_class(instance=goods)

        context = {
            "process": application,
            "form": form,
            "case_type": "import",
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Edit Goods",
        }

        return render(
            request,
            "web/domains/case/import/manage/response-prep-edit-form.html",
            context,
        )


@login_required
@require_POST
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def response_preparation_reset_goods(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    sil_section_type: str,
    section_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        config = _get_sil_section_resp_prep_config(sil_section_type)
        goods: types.GoodsModel = get_object_or_404(config.model_class, pk=section_pk)

        goods.description = goods.description_original
        goods.quantity = goods.quantity_original
        goods.save()

        return redirect(
            reverse(
                "case:prepare-response",
                kwargs={"application_pk": application.pk, "case_type": "import"},
            )
        )


@login_required
def submit(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = _get_sil_errors(application)

        if request.method == "POST":
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                # Check if we need to remove any section five documents
                if not application.section5:
                    # Archive the section5 files
                    application.user_section5.all().update(is_active=False)

                    # Clear any verified section 5 links.
                    application.verified_section5.clear()

                submit_application(application, request, task)

                add_template_data_on_submit(application)

                # Only create if needed
                # This view gets called when an applicant submits changes
                _, created = models.SILSupplementaryInfo.objects.get_or_create(
                    import_application=application
                )

                return redirect_after_submit(application, request)

        else:
            form = SubmitForm()

        context = {
            "process": application,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Submit Application",
            "form": form,
            "declaration": application.application_type.declaration_template,
            "errors": errors if errors.has_errors() else None,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/import-case-submit.html", context)


@login_required
def add_section5_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = case_forms.DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")

                create_file_model(document, request.user, application.user_section5)

                return redirect(
                    reverse(
                        "import:fa:manage-certificates", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            form = case_forms.DocumentForm()

        context = {
            "process": application,
            "form": form,
            "case_type": "import",
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Create Section 5",
        }

        return render(request, "web/domains/case/import/fa-sil/add-section5-document.html", context)


@require_POST
@login_required
def archive_section5_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)
        case_progress.application_in_progress(application)

        document = application.user_section5.get(pk=section5_pk)
        document.is_active = False
        document.save()

        return redirect(
            reverse("import:fa:manage-certificates", kwargs={"application_pk": application_pk})
        )


@require_GET
@login_required
def view_section5_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    application: models.SILApplication = get_object_or_404(models.SILApplication, pk=application_pk)
    get_object_or_404(application.user_section5, pk=section5_pk)

    # Permission checks in view_application_file
    return view_application_file(request.user, application, application.user_section5, section5_pk)


@login_required
@require_POST
def add_verified_section5(
    request: AuthenticatedHttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)
        section5 = get_object_or_404(
            application.importer.section5_authorities.filter(is_active=True), pk=section5_pk
        )

        case_progress.application_in_progress(application)

        application.verified_section5.add(section5)

        return redirect(
            reverse("import:fa:manage-certificates", kwargs={"application_pk": application_pk})
        )


@login_required
@require_POST
def delete_verified_section5(
    request: AuthenticatedHttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)
        section5 = get_object_or_404(application.verified_section5, pk=section5_pk)

        case_progress.application_in_progress(application)

        application.verified_section5.remove(section5)

        return redirect(
            reverse("import:fa:manage-certificates", kwargs={"application_pk": application_pk})
        )


@login_required
def view_verified_section5(
    request: AuthenticatedHttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_view_application(request.user, application)

        section5 = get_object_or_404(
            application.importer.section5_authorities.filter(is_active=True), pk=section5_pk
        )

        context = {
            "process": application,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - View Verified Section 5",
            "section5": section5,
            "case_type": "import",
        }

        return render(
            request, "web/domains/case/import/fa-sil/view-verified-section5.html", context
        )


@require_GET
@login_required
def view_verified_section5_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application = get_object_or_404(models.SILApplication, pk=application_pk)
    section5 = get_object_or_404(
        application.importer.section5_authorities.filter(is_active=True), files__pk=document_pk
    )

    # Permission checks in view_application_file
    return view_application_file(request.user, application, section5.files, document_pk)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        readonly_view = get_caseworker_view_readonly_status(application, "import", request.user)
        checklist, created = models.SILChecklist.objects.get_or_create(
            import_application=application
        )

        if request.method == "POST" and not readonly_view:
            form: forms.SILChecklistForm = forms.SILChecklistOptionalForm(
                request.POST, instance=checklist
            )

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa-sil:manage-checklist", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            if created:
                form = forms.SILChecklistForm(instance=checklist, readonly_form=readonly_view)
            else:
                form = forms.SILChecklistForm(
                    data=model_to_dict(checklist), instance=checklist, readonly_form=readonly_view
                )

        context = {
            "process": application,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Checklist",
            "form": form,
            "readonly_view": readonly_view,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/checklist.html",
            context=context,
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def set_cover_letter(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_progress.application_in_processing(application)

        if request.method == "POST":
            form = forms.SILCoverLetterTemplateForm(request.POST)

            if form.is_valid():
                template = form.cleaned_data["template"]
                add_application_cover_letter(application, template)

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )

        else:
            form = forms.SILCoverLetterTemplateForm()

        context = {
            "process": application,
            "page_title": "Set Cover Letter",
            "form": form,
            "case_type": "import",
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/response-prep-edit-form.html",
            context=context,
        )


@login_required
def add_report_firearm_manual(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    report_pk: int,
    sil_section_type: str,
    section_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)
        case_progress.application_is_complete(application)

        supplementary_info: models.SILSupplementaryInfo = application.supplementary_info
        report: models.SILSupplementaryReport = supplementary_info.reports.get(pk=report_pk)

        section_cert = report.get_section_certificates(sil_section_type).get(pk=section_pk)

        form_class = _get_report_firearm_form_class(sil_section_type)

        if request.method == "POST":
            form = form_class(data=request.POST)

            if form.is_valid():
                report_firearm = form.save(commit=False)
                report_firearm.report = report
                report_firearm.is_manual = True
                report_firearm.goods_certificate = section_cert
                report_firearm.save()

                return redirect(
                    reverse(
                        "import:fa:edit-report",
                        kwargs={"application_pk": application.pk, "report_pk": report.pk},
                    )
                )

        else:
            form = form_class()

        context = {
            "process": application,
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Add Firearm Details",
            "form": form,
            "report": report,
            "goods_description": section_cert.description,
        }

        template = "web/domains/case/import/fa/provide-report/edit-report-firearm-manual.html"

        return render(request=request, template_name=template, context=context)


@login_required
def add_report_firearm_upload(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    report_pk: int,
    sil_section_type: str,
    section_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)
        case_progress.application_is_complete(application)

        supplementary_info: models.SILSupplementaryInfo = application.supplementary_info
        report: models.SILSupplementaryReport = supplementary_info.reports.get(pk=report_pk)

        section_cert = report.get_section_certificates(sil_section_type).get(pk=section_pk)

        form_class = _get_report_upload_firearm_form_class(sil_section_type)

        if request.method == "POST":
            form = form_class(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data["file"]

                report_firearm = form.save(commit=False)
                report_firearm.report = report
                report_firearm.goods_certificate = section_cert
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
            form = form_class()

        context = {
            "process": application,
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Add Firearm Details",
            "form": form,
            "report": report,
            "goods_description": section_cert.description,
        }

        template = "web/domains/case/import/fa/provide-report/add-report-firearm-upload.html"

        return render(request=request, template_name=template, context=context)


@require_GET
@login_required
def view_upload_document(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    report_firearm_pk: int,
    sil_section_type: str,
    **kwargs: dict[str, Any],
) -> HttpResponse:
    application: models.SILApplication = get_object_or_404(models.SILApplication, pk=application_pk)
    supplementary_firearm_report_model = _get_report_firearm_model(sil_section_type)
    supplementary_firearm_report = supplementary_firearm_report_model.objects.get(
        pk=report_firearm_pk
    )
    document = supplementary_firearm_report.document

    return view_application_file(request.user, application, File.objects, document.pk)


@login_required
def edit_report_firearm_manual(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    sil_section_type: str,
    report_pk: int,
    section_pk: int,
    report_firearm_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)
        case_progress.application_is_complete(application)

        supplementary_info: models.SILSupplementaryInfo = application.supplementary_info
        report: models.SILSupplementaryReport = supplementary_info.reports.get(pk=report_pk)

        section_cert = report.get_section_certificates(sil_section_type).get(pk=section_pk)

        report_firearm = section_cert.supplementary_report_firearms.get(pk=report_firearm_pk)

        form_class = _get_report_firearm_form_class(sil_section_type)

        if request.method == "POST":
            form = form_class(instance=report_firearm, data=request.POST)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa:edit-report",
                        kwargs={"application_pk": application.pk, "report_pk": report.pk},
                    )
                )

        else:
            form = form_class(instance=report_firearm)

        context = {
            "process": application,
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Edit Firearm Details",
            "form": form,
            "report": report,
            "goods_description": section_cert.description,
        }

        template = "web/domains/case/import/fa/provide-report/edit-report-firearm-manual.html"

        return render(request=request, template_name=template, context=context)


@login_required
@require_POST
def add_report_firearm_no_firearm(
    request: AuthenticatedHttpRequest,
    *,
    application_pk: int,
    report_pk: int,
    sil_section_type: str,
    section_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)
        case_progress.application_is_complete(application)

        supplementary_info: models.SILSupplementaryInfo = application.supplementary_info
        report: models.SILSupplementaryReport = supplementary_info.reports.get(pk=report_pk)

        section_cert = report.get_section_certificates(sil_section_type).get(pk=section_pk)

        model_class = _get_report_firearm_model(sil_section_type)
        model_class.objects.create(
            report=report, goods_certificate=section_cert, is_no_firearm=True
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
    sil_section_type: str,
    section_pk: int,
    report_pk: int,
    report_firearm_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)
        case_progress.application_is_complete(application)

        supplementary_info: models.SILSupplementaryInfo = application.supplementary_info
        report: models.SILSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
        section_cert = report.get_section_certificates(sil_section_type).get(pk=section_pk)

        report_firearm = section_cert.supplementary_report_firearms.get(pk=report_firearm_pk)

        report_firearm.delete()

        return redirect(
            reverse(
                "import:fa:edit-report",
                kwargs={"application_pk": application.pk, "report_pk": report.pk},
            )
        )
