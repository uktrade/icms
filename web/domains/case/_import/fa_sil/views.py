from typing import NamedTuple, Type, Union

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from web.domains.case import forms as case_forms
from web.domains.case import views as case_views
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.flow.models import Task
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from ..models import ImportApplication
from . import forms, models

GoodsModel = Union[
    models.SILGoodsSection1,
    models.SILGoodsSection2,
    models.SILGoodsSection5,
    models.SILGoodsSection582Obsolete,
    models.SILGoodsSection582Other,
]
GoodsModelT = Type[GoodsModel]

GoodsForm = Union[
    forms.SILGoodsSection1Form,
    forms.SILGoodsSection2Form,
    forms.SILGoodsSection5Form,
    forms.SILGoodsSection582ObsoleteForm,
    forms.SILGoodsSection582OtherForm,
]
GoodsFormT = Type[GoodsForm]


class CreateSILSectionConfig(NamedTuple):
    model_class: GoodsModelT
    form_class: GoodsFormT
    template: str


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
            model_class=models.SILGoodsSection582Obsolete,
            form_class=forms.SILGoodsSection582ObsoleteForm,
            template="web/domains/case/import/fa-sil/goods/section582-obsolete.html",
        )

    elif sil_section_type == "section582-other":
        return CreateSILSectionConfig(
            model_class=models.SILGoodsSection582Other,
            form_class=forms.SILGoodsSection582OtherForm,
            template="web/domains/case/import/fa-sil/goods/section582-other.html",
        )
    raise NotImplementedError(f"sil_section_type is not supported: {sil_section_type}")


def _get_sil_errors(application: models.SILApplication) -> ApplicationErrors:
    errors = ApplicationErrors()

    edit_url = reverse("import:fa-sil:edit", kwargs={"application_pk": application.pk})

    # Check main form
    application_details_errors = PageErrors(page_name="Application details", url=edit_url)
    application_form = forms.PrepareSILForm(data=model_to_dict(application), instance=application)
    create_page_errors(application_form, application_details_errors)
    errors.add(application_details_errors)

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
        section_errors = PageErrors(
            page_name="Application Details - Certificates - Section 5", url=edit_url
        )
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
        section_errors = PageErrors(
            page_name="Application Details - Documents - Section 5", url=edit_url
        )
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
    has_certificates = (
        application.user_imported_certificates.filter(is_active=True).exists()
        or application.verified_certificates.filter(is_active=True).exists()
    )

    if application.section1 and not has_certificates:
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

    # Select existing certificate errors
    # TODO: implement ICMSLST-476

    # Check know bought from
    # TODO: implement ICMSLST-676

    return errors


@login_required
def edit(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if request.POST:
            form = forms.PrepareSILForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:fa-sil:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = forms.PrepareSILForm(instance=application, initial={"contact": request.user})

        verified_section5 = application.importer.section5_authorities.currently_active()
        available_verified_section5 = verified_section5.exclude(
            pk__in=application.verified_section5.all()
        )

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "user_section5": application.user_section5.filter(is_active=True),
            "verified_section5": verified_section5,
            "available_verified_section5": available_verified_section5,
            "selected_section5": application.verified_section5.all(),
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Edit",
        }

        return render(request, "web/domains/case/import/fa-sil/edit.html", context)


@login_required
def choose_goods_section(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Edit Goods",
        }

        return render(request, "web/domains/case/import/fa-sil/choose-goods-section.html", context)


@login_required
def add_section(
    request: HttpRequest, *, application_pk: int, sil_section_type: str
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        config = _get_sil_section_app_config(sil_section_type)

        if request.POST:
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
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Add Goods",
        }

        return render(request, config.template, context)


@login_required
def edit_section(
    request: HttpRequest,
    *,
    application_pk: int,
    sil_section_type: str,
    section_pk: int,
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")
        config = _get_sil_section_app_config(sil_section_type)
        goods: GoodsModel = get_object_or_404(config.model_class, pk=section_pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if request.POST:
            form = config.form_class(request.POST, instance=goods)
            if form.is_valid():
                goods = form.save(commit=False)
                goods.import_application = application
        else:
            form = config.form_class(instance=goods)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Edit Goods",
        }

        return render(request, config.template, context)


@login_required
@require_POST
def delete_section(
    request: HttpRequest, *, application_pk: int, sil_section_type: str, section_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")
        config = _get_sil_section_app_config(sil_section_type)
        goods: GoodsModel = get_object_or_404(config.model_class, pk=section_pk)

        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        goods.is_active = False
        goods.save()

        return redirect(reverse("import:fa-sil:edit", kwargs={"application_pk": application_pk}))


@login_required
def submit(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        errors = _get_sil_errors(application)

        if request.POST:
            form = forms.SubmitSILForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                application.status = ImportApplication.SUBMITTED
                application.submit_datetime = timezone.now()

                application.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                Task.objects.create(process=application, task_type="process", previous=task)

                return redirect(reverse("home"))

        else:
            form = forms.SubmitSILForm()

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
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Submit Application",
            "form": form,
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/import/fa-sil/submit.html", context)


@login_required
def add_section5_document(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if request.POST:
            form = case_forms.DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")

                create_file_model(document, request.user, application.user_section5)

                return redirect(
                    reverse("import:fa-sil:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = case_forms.DocumentForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Create Section 5",
        }

        return render(request, "web/domains/case/import/fa-sil/add-section5-document.html", context)


@require_POST
@login_required
def archive_section5_document(
    request: HttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")
        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        document = application.user_section5.get(pk=section5_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:fa-sil:edit", kwargs={"application_pk": application_pk}))


@require_GET
@login_required
def view_section5_document(
    request: HttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    application: models.SILApplication = get_object_or_404(models.SILApplication, pk=application_pk)
    get_object_or_404(application.user_section5, pk=section5_pk)

    return case_views.view_application_file(
        request.user, application, application.user_section5, section5_pk, "import"
    )


@login_required
@require_POST
def add_verified_section5(
    request: HttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")
        section5 = get_object_or_404(
            application.importer.section5_authorities.filter(is_active=True), pk=section5_pk
        )

        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        application.verified_section5.add(section5)

        return redirect(reverse("import:fa-sil:edit", kwargs={"application_pk": application_pk}))


@login_required
@require_POST
def delete_verified_section5(
    request: HttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")
        section5 = get_object_or_404(application.verified_section5, pk=section5_pk)

        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        application.verified_section5.remove(section5)

        return redirect(reverse("import:fa-sil:edit", kwargs={"application_pk": application_pk}))


@login_required
def view_verified_section5(
    request: HttpRequest, *, application_pk: int, section5_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        case_views.check_application_permission(application, request.user, "import")
        section5 = get_object_or_404(
            application.importer.section5_authorities.filter(is_active=True), pk=section5_pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - View Verified Section 5",
            "section5": section5,
        }

        return render(
            request, "web/domains/case/import/fa-sil/view-verified-section5.html", context
        )


@require_GET
@login_required
def view_verified_section5_document(
    request: HttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application = get_object_or_404(models.SILApplication, pk=application_pk)
    section5 = get_object_or_404(
        application.importer.section5_authorities.filter(is_active=True), files__pk=document_pk
    )

    return case_views.view_application_file(
        request.user, application, section5.files, document_pk, "import"
    )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_checklist(request: HttpRequest, *, application_pk):
    with transaction.atomic():
        application: models.SILApplication = get_object_or_404(
            models.SILApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(ImportApplication.SUBMITTED, "process")
        checklist, created = models.SILChecklist.objects.get_or_create(
            import_application=application
        )

        if request.POST:
            # We allow partial model saving as its a checklist
            form = forms.SILChecklistOptionalForm(request.POST, instance=checklist)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa-sil:manage-checklist", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            if not created:
                form = forms.SILChecklistForm(data=model_to_dict(checklist), instance=checklist)
            else:
                form = forms.SILChecklistForm(instance=checklist)

        context = {
            "process": application,
            "task": task,
            "page_title": "Firearms and Ammunition (Specific Import Licence) - Checklist",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )
