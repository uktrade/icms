from typing import NamedTuple

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case import forms as case_forms
from web.domains.case._import.fa.forms import (
    ImportContactKnowBoughtFromForm,
    UserImportCertificateForm,
)
from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import SubmitForm
from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.utils import (
    check_application_permission,
    get_application_form,
    redirect_after_submit,
    submit_application,
    view_application_file,
)
from web.domains.case.views.utils import get_caseworker_view_readonly_status
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

from . import forms, models, types


class CreateSILSectionConfig(NamedTuple):
    model_class: types.GoodsModelT
    form_class: types.GoodsFormT
    template: str


class ResponsePrepEditSILSectionConfig(NamedTuple):
    model_class: types.GoodsModelT
    form_class: types.ResponsePrepGoodsFormT


def _get_sil_section_app_config(sil_section_type: str) -> CreateSILSectionConfig:
    if sil_section_type == "section1":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection1,
            form_class=forms.SILGoodsSection1Form,
            template="web/domains/case/import/fa-sil/goods/section1.html",
        )

    elif sil_section_type == "section2":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection2,
            form_class=forms.SILGoodsSection2Form,
            template="web/domains/case/import/fa-sil/goods/section2.html",
        )

    elif sil_section_type == "section5":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection5,
            form_class=forms.SILGoodsSection5Form,
            template="web/domains/case/import/fa-sil/goods/section5.html",
        )

    elif sil_section_type == "section582-obsolete":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection582Obsolete,  # /PS-IGNORE
            form_class=forms.SILGoodsSection582ObsoleteForm,  # /PS-IGNORE
            template="web/domains/case/import/fa-sil/goods/section582-obsolete.html",
        )

    elif sil_section_type == "section582-other":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection582Other,  # /PS-IGNORE
            form_class=forms.SILGoodsSection582OtherForm,  # /PS-IGNORE
            template="web/domains/case/import/fa-sil/goods/section582-other.html",
        )

    elif sil_section_type == "section_legacy":
        return CreateSILSectionConfig(
            model_class=models.SILLegacyGoods,
            # These are invalid, but we don't want to be able to edit them
            form_class=None,  # type: ignore[arg-type]
            template=None,  # type: ignore[arg-type]
        )

    raise NotImplementedError(f"sil_section_type is not supported: {sil_section_type}")


def _get_sil_section_resp_prep_config(sil_section_type: str) -> ResponsePrepEditSILSectionConfig:
    if sil_section_type == "section1":
        return ResponsePrepEditSILSectionConfig(
            model_class=models.SILGoodsSection1,
            form_class=forms.ResponsePrepSILGoodsSection1Form,
        )

    elif sil_section_type == "section2":
        return ResponsePrepEditSILSectionConfig(
            model_class=models.SILGoodsSection2,
            form_class=forms.ResponsePrepSILGoodsSection2Form,
        )

    elif sil_section_type == "section5":
        return ResponsePrepEditSILSectionConfig(
            model_class=models.SILGoodsSection5,
            form_class=forms.ResponsePrepSILGoodsSection5Form,
        )

    elif sil_section_type == "section582-obsolete":
        return ResponsePrepEditSILSectionConfig(
            model_class=models.SILGoodsSection582Obsolete,  # /PS-IGNORE
            form_class=forms.ResponsePrepSILGoodsSection582ObsoleteForm,  # /PS-IGNORE
        )

    elif sil_section_type == "section582-other":
        return ResponsePrepEditSILSectionConfig(
            model_class=models.SILGoodsSection582Other,  # /PS-IGNORE
            form_class=forms.ResponsePrepSILGoodsSection582OtherForm,  # /PS-IGNORE
        )

    raise NotImplementedError(f"sil_section_type is not supported: {sil_section_type}")


def _get_report_firearm_form_class(sil_section_type: str) -> types.SILReportFirearmFormT:
    if sil_section_type == "section1":
        return forms.SILSupplementaryReportFirearmSection1Form

    elif sil_section_type == "section2":
        return forms.SILSupplementaryReportFirearmSection2Form

    elif sil_section_type == "section5":
        return forms.SILSupplementaryReportFirearmSection5Form

    elif sil_section_type == "section582-obsolete":
        return forms.SILSupplementaryReportFirearmSection582ObsoleteForm  # /PS-IGNORE

    elif sil_section_type == "section582-other":
        return forms.SILSupplementaryReportFirearmSection582OtherForm  # /PS-IGNORE

    elif sil_section_type == "section_legacy":
        return forms.SILSupplementaryReportFirearmSectionLegacyForm

    raise NotImplementedError(f"sil_section_type is not supported: {sil_section_type}")


def _get_report_firearm_model(sil_section_type: str) -> types.SILReportFirearmModelT:
    if sil_section_type == "section1":
        return models.SILSupplementaryReportFirearmSection1

    elif sil_section_type == "section2":
        return models.SILSupplementaryReportFirearmSection2

    elif sil_section_type == "section5":
        return models.SILSupplementaryReportFirearmSection5

    elif sil_section_type == "section582-obsolete":
        return models.SILSupplementaryReportFirearmSection582Obsolete  # /PS-IGNORE

    elif sil_section_type == "section582-other":
        return models.SILSupplementaryReportFirearmSection582Other  # /PS-IGNORE

    elif sil_section_type == "section_legacy":
        return models.SILSupplementaryReportFirearmSectionLegacy

    raise NotImplementedError(f"sil_section_type is not supported: {sil_section_type}")


def _get_sil_errors(application: models.SILApplication) -> ApplicationErrors:
    errors = ApplicationErrors()

    edit_url = reverse("import:fa-sil:edit", kwargs={"application_pk": application.pk})
    edit_url = f"{edit_url}?validate"

    # Check main form
    application_details_errors = PageErrors(page_name="Application details", url=edit_url)
    application_form = forms.SubmitFaSILForm(data=model_to_dict(application), instance=application)
    create_page_errors(application_form, application_details_errors)
    errors.add(application_details_errors)

    # Check know bought from
    bought_from_errors = PageErrors(
        page_name="Details of who bought from",
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

    # Goods validation
    if application.section1 and not application.goods_section1.filter(is_active=True).exists():
        url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": application.pk, "sil_section_type": "section1"},
        )
        section_errors = PageErrors(page_name="Add Licence for Section 1", url=url)
        section_errors.add(
            FieldError(field_name="Goods", messages=["At least one 'section 1' must be added"])
        )
        errors.add(section_errors)

    if application.section2 and not application.goods_section2.filter(is_active=True).exists():
        url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": application.pk, "sil_section_type": "section2"},
        )
        section_errors = PageErrors(page_name="Add Licence for Section 2", url=url)
        section_errors.add(
            FieldError(field_name="Goods", messages=["At least one 'section 2' must be added"])
        )
        errors.add(section_errors)

    if application.section5 and not application.goods_section5.filter(is_active=True).exists():
        url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": application.pk, "sil_section_type": "section5"},
        )
        section_errors = PageErrors(page_name="Add Licence for Section 5", url=url)
        section_errors.add(
            FieldError(field_name="Goods", messages=["At least one 'section 5' must be added"])
        )
        errors.add(section_errors)

    if (
        application.section58_obsolete
        and not application.goods_section582_obsoletes.filter(is_active=True).exists()
    ):
        url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": application.pk, "sil_section_type": "section582-obsolete"},
        )
        section_errors = PageErrors(page_name="Add Licence for Section 58(2) - Obsolete", url=url)
        section_errors.add(
            FieldError(
                field_name="Goods",
                messages=["At least one 'section 58(2) - obsolete' must be added"],
            )
        )
        errors.add(section_errors)

    if (
        application.section58_other
        and not application.goods_section582_others.filter(is_active=True).exists()
    ):
        url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": application.pk, "sil_section_type": "section582-other"},
        )
        section_errors = PageErrors(page_name="Add Licence for Section 58(2) - Other", url=url)
        section_errors.add(
            FieldError(
                field_name="Add Section 5",
                messages=["At least one section 'section 58(2) - other' must be added"],
            )
        )
        errors.add(section_errors)

    importer_has_section5 = application.importer.section5_authorities.currently_active().exists()
    selected_section5 = application.verified_section5.currently_active().exists()

    # Verified Section 5
    if application.section5 and importer_has_section5 and not selected_section5:
        url = reverse("import:fa:manage-certificates", kwargs={"application_pk": application.pk})
        section_errors = PageErrors(page_name="Certificates - Section 5 Authority", url=url)
        section_errors.add(
            FieldError(
                field_name="Verified Section 5 Authorities",
                messages=[
                    "Please ensure you have selected at least one verified Section 5 Authority"
                ],
            )
        )
        errors.add(section_errors)

    # User Section 5
    if (
        application.section5
        and not importer_has_section5
        and not application.user_section5.filter(is_active=True).exists()
    ):
        url = reverse(
            "import:fa-sil:add-section5-document", kwargs={"application_pk": application.pk}
        )
        section_errors = PageErrors(page_name="Certificates - Section 5 Authority", url=url)
        section_errors.add(
            FieldError(
                field_name="Section 5 Authorities",
                messages=[
                    "Please ensure you have uploaded at least one Section 5 Authority document."
                ],
            )
        )
        errors.add(section_errors)

    # Certificates errors
    correct_section = any((application.section1, application.section2, application.section5))

    has_certificates = (
        application.user_imported_certificates.filter(is_active=True).exists()
        or application.verified_certificates.filter(is_active=True).exists()
    )

    if correct_section and not has_certificates:
        certificate_errors = PageErrors(
            page_name="Certificates",
            url=reverse("import:fa:manage-certificates", kwargs={"application_pk": application.pk}),
        )

        certificate_errors.add(
            FieldError(
                field_name="Certificate", messages=["At least one certificate must be added"]
            )
        )

        errors.add(certificate_errors)

    user_imported_certificates = application.user_imported_certificates.filter(is_active=True)

    for cert in user_imported_certificates:
        page_errors = PageErrors(
            page_name=f"Certificate - {cert.reference}",
            url=reverse(
                "import:fa:edit-certificate",
                kwargs={"application_pk": application.pk, "certificate_pk": cert.pk},
            ),
        )

        create_page_errors(
            UserImportCertificateForm(
                data=model_to_dict(cert), instance=cert, application=application
            ),
            page_errors,
        )
        errors.add(page_errors)

    errors.add(get_org_update_request_errors(application, "import"))

    return errors


@login_required
def edit(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "import")

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


@login_required
def choose_goods_section(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    application: models.SILApplication = get_object_or_404(models.SILApplication, pk=application_pk)
    check_application_permission(application, request.user, "import")

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
        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        config = _get_sil_section_app_config(sil_section_type)

        if request.method == "POST":
            form = config.form_class(request.POST)

            if form.is_valid():
                goods = form.save(commit=False)
                goods.import_application = application
                goods.save()

                return redirect(
                    reverse("import:fa-sil:edit", kwargs={"application_pk": application.pk})
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
        check_application_permission(application, request.user, "import")
        config = _get_sil_section_app_config(sil_section_type)
        goods: types.GoodsModel = get_object_or_404(config.model_class, pk=section_pk)

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = config.form_class(request.POST, instance=goods)
            if form.is_valid():
                goods = form.save(commit=False)
                goods.import_application = application
                goods.save()
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
        check_application_permission(application, request.user, "import")
        config = _get_sil_section_app_config(sil_section_type)
        goods: types.GoodsModel = get_object_or_404(config.model_class, pk=section_pk)

        case_progress.application_in_progress(application)

        goods.is_active = False
        goods.save()

        return redirect(reverse("import:fa-sil:edit", kwargs={"application_pk": application_pk}))


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
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
def submit(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "import")

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

                # Only create if needed
                # This view gets called when an applicant submits changes
                _, created = models.SILSupplementaryInfo.objects.get_or_create(
                    import_application=application
                )

                # Only add the endorsement template once too.
                if created:
                    # TODO: replace with Endorsement Usage Template (ICMSLST-638)
                    endorsement = Template.objects.get(
                        is_active=True,
                        template_type=Template.ENDORSEMENT,
                        template_name="Firearms Sanctions COO & COC (AC & AY)",
                    )
                    application.endorsements.create(content=endorsement.template_content)

                return redirect_after_submit(application, request)

        else:
            form = SubmitForm()

        declaration = Template.objects.filter(
            is_active=True,
            template_type=Template.DECLARATION,
            application_domain=Template.IMPORT_APPLICATION,
            template_code="IMA_GEN_DECLARATION",
        ).first()

        context = {
            "process": application,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Submit Application",
            "form": form,
            "declaration": declaration,
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
        check_application_permission(application, request.user, "import")

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
        check_application_permission(application, request.user, "import")
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

    return view_application_file(
        request.user, application, application.user_section5, section5_pk, "import"
    )


@login_required
@require_POST
def add_verified_section5(
    request: AuthenticatedHttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "import")
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
        check_application_permission(application, request.user, "import")
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
        check_application_permission(application, request.user, "import")
        section5 = get_object_or_404(
            application.importer.section5_authorities.filter(is_active=True), pk=section5_pk
        )

        case_progress.application_in_progress(application)

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

    return view_application_file(request.user, application, section5.files, document_pk, "import")


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
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
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
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

                # TODO: Revisit the content variables when we come back to this.
                # Having to know what to pass to an editable template feels wrong.
                # e.g.
                # application.cover_letter = template.get_content(application)
                application.cover_letter = template.get_content(
                    {
                        "CONTACT_NAME": application.contact,
                        "LICENCE_NUMBER": None,  # TODO: What should this be?
                        "APPLICATION_SUBMITTED_DATE": application.submit_datetime,
                        "LICENCE_END_DATE": document_pack.pack_draft_get(
                            application
                        ).licence_end_date,
                        "COUNTRY_OF_ORIGIN": application.origin_country.name,
                        "COUNTRY_OF_CONSIGNMENT": application.consignment_country.name,
                    }
                )
                application.save()

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

        check_application_permission(application, request.user, "import")
        application.check_expected_status([ImpExpStatus.COMPLETED])

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

        check_application_permission(application, request.user, "import")
        application.check_expected_status([ImpExpStatus.COMPLETED])

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

        check_application_permission(application, request.user, "import")
        application.check_expected_status([ImpExpStatus.COMPLETED])

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

        check_application_permission(application, request.user, "import")
        application.check_expected_status([ImpExpStatus.COMPLETED])

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
