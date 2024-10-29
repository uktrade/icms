from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.fa.forms import (
    ImportContactKnowBoughtFromForm,
    UserImportCertificateForm,
)
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
from web.models import (
    ChecklistFirearmsOILApplication,
    File,
    OILSupplementaryInfo,
    OILSupplementaryReport,
    OILSupplementaryReportFirearm,
    OpenIndividualLicenceApplication,
    Task,
    User,
)
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .forms import (
    ChecklistFirearmsOILApplicationForm,
    ChecklistFirearmsOILApplicationOptionalForm,
    EditFaOILForm,
    OILSupplementaryReportFirearmForm,
    OILSupplementaryReportUploadFirearmForm,
    SubmitFaOILForm,
)


def check_can_edit_application(user: User, application: OpenIndividualLicenceApplication) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


@login_required
def edit_oil(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )
        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        form = get_application_form(application, request, EditFaOILForm, SubmitFaOILForm)

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("import:fa-oil:edit", kwargs={"application_pk": application_pk})
                )

        context = {
            "process": application,
            "form": form,
            "page_title": "Open Individual Import Licence - Edit",
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/fa-oil/edit.html", context)


@login_required
def submit_oil(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = ApplicationErrors()

        edit_url = reverse("import:fa-oil:edit", kwargs={"application_pk": application_pk})
        edit_url = f"{edit_url}?validate"

        page_errors = PageErrors(page_name="Application Details", url=edit_url)
        create_page_errors(
            SubmitFaOILForm(data=model_to_dict(application), instance=application), page_errors
        )
        errors.add(page_errors)

        has_certificates = (
            application.user_imported_certificates.filter(is_active=True).exists()
            or application.verified_certificates.filter(is_active=True).exists()
        )

        if not has_certificates:
            page_errors = PageErrors(
                page_name="Certificates",
                url=reverse(
                    "import:fa:manage-certificates", kwargs={"application_pk": application_pk}
                ),
            )

            page_errors.add(
                FieldError(
                    field_name="Certificate", messages=["At least one certificate must be added"]
                )
            )

            errors.add(page_errors)

        user_imported_certificates = application.user_imported_certificates.filter(is_active=True)

        for cert in user_imported_certificates:
            page_errors = PageErrors(
                page_name=f"Certificate - {cert.reference}",
                url=reverse(
                    "import:fa:edit-certificate",
                    kwargs={"application_pk": application_pk, "certificate_pk": cert.pk},
                ),
            )

            create_page_errors(
                UserImportCertificateForm(
                    data=model_to_dict(cert), instance=cert, application=application
                ),
                page_errors,
            )
            errors.add(page_errors)

        # Check know bought from
        bought_from_errors = PageErrors(
            page_name="Details of who bought from",
            url=reverse(
                "import:fa:manage-import-contacts", kwargs={"application_pk": application.pk}
            ),
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

        if request.method == "POST":
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                submit_application(application, request, task)
                add_template_data_on_submit(application)

                # Only create if needed
                # This view gets called when an applicant submits changes
                OILSupplementaryInfo.objects.get_or_create(import_application=application)

                return redirect_after_submit(application, request)

        else:
            form = SubmitForm()

        context = {
            "process": application,
            "page_title": "Open Individual Import Licence - Submit Application",
            "form": form,
            "declaration": application.application_type.declaration_template,
            "errors": errors if errors.has_errors() else None,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/import-case-submit.html", context)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OpenIndividualLicenceApplication = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )
        readonly_view = get_caseworker_view_readonly_status(application, "import", request.user)
        checklist, created = ChecklistFirearmsOILApplication.objects.get_or_create(
            import_application=application
        )

        if request.method == "POST" and not readonly_view:
            form: ChecklistFirearmsOILApplicationForm = ChecklistFirearmsOILApplicationOptionalForm(
                request.POST, instance=checklist
            )

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa-oil:manage-checklist", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            if created:
                form = ChecklistFirearmsOILApplicationForm(
                    instance=checklist, readonly_form=readonly_view
                )
            else:
                form = ChecklistFirearmsOILApplicationForm(
                    data=model_to_dict(checklist), instance=checklist, readonly_form=readonly_view
                )

        context = {
            "process": application,
            "page_title": "Open Individual Import Licence - Checklist",
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
    request: AuthenticatedHttpRequest, *, application_pk: int, report_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OpenIndividualLicenceApplication = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_is_complete(application)

        supplementary_info: OILSupplementaryInfo = application.supplementary_info
        report: OILSupplementaryReport = supplementary_info.reports.get(pk=report_pk)

        if request.method == "POST":
            form = OILSupplementaryReportFirearmForm(data=request.POST)

            if form.is_valid():
                report_firearm: OILSupplementaryReportFirearm = form.save(commit=False)
                report_firearm.report = report
                report_firearm.is_manual = True
                report_firearm.save()

                return redirect(
                    reverse(
                        "import:fa:edit-report",
                        kwargs={"application_pk": application.pk, "report_pk": report.pk},
                    )
                )

        else:
            form = OILSupplementaryReportFirearmForm()

        context = {
            "process": application,
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Add Firearm Details",
            "form": form,
            "report": report,
            "goods_description": application.goods_description(),
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
        application: OpenIndividualLicenceApplication = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_is_complete(application)
        supplementary_info: OILSupplementaryInfo = application.supplementary_info
        report: OILSupplementaryReport = supplementary_info.reports.get(pk=report_pk)

        report_firearm: OILSupplementaryReportFirearm = report.firearms.get(pk=report_firearm_pk)

        if request.method == "POST":
            form = OILSupplementaryReportFirearmForm(data=request.POST, instance=report_firearm)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa:edit-report",
                        kwargs={"application_pk": application.pk, "report_pk": report.pk},
                    )
                )

        else:
            form = OILSupplementaryReportFirearmForm(instance=report_firearm)

        context = {
            "process": application,
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Edit Firearm Details",
            "form": form,
            "report": report,
            "goods_description": application.goods_description(),
        }

        template = "web/domains/case/import/fa/provide-report/edit-report-firearm-manual.html"

        return render(request=request, template_name=template, context=context)


@login_required
def add_report_firearm_upload(
    request: AuthenticatedHttpRequest, *, application_pk: int, report_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OpenIndividualLicenceApplication = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_is_complete(application)

        supplementary_info: OILSupplementaryInfo = application.supplementary_info
        report: OILSupplementaryReport = supplementary_info.reports.get(pk=report_pk)

        if request.method == "POST":
            form = OILSupplementaryReportUploadFirearmForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data["file"]

                report_firearm: OILSupplementaryReportFirearm = form.save(commit=False)
                report_firearm.report = report
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
            form = OILSupplementaryReportUploadFirearmForm()

        context = {
            "process": application,
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Add Firearm Details",
            "form": form,
            "report": report,
            "goods_description": application.goods_description(),
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
    application: OpenIndividualLicenceApplication = get_object_or_404(
        OpenIndividualLicenceApplication, pk=application_pk
    )

    supplementary_info: OILSupplementaryInfo = application.supplementary_info
    report: OILSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
    report_firearm: OILSupplementaryReportFirearm = report.firearms.get(pk=report_firearm_pk)
    document = report_firearm.document

    # Permissions checks in view_application_file
    return view_application_file(request.user, application, File.objects, document.pk)


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
        application: OpenIndividualLicenceApplication = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_is_complete(application)

        supplementary_info: OILSupplementaryInfo = application.supplementary_info
        report: OILSupplementaryReport = supplementary_info.reports.get(pk=report_pk)

        report_firearm: OILSupplementaryReportFirearm = report.firearms.get(pk=report_firearm_pk)

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
