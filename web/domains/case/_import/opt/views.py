from typing import Any

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplication
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.views import check_application_permission, view_application_file
from web.domains.commodity.models import CommodityGroup
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.types import AuthenticatedHttpRequest
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .forms import (
    CompensatingProductsOPTForm,
    EditOPTForm,
    FurtherQuestionsOPTForm,
    OPTChecklistForm,
    OPTChecklistOptionalForm,
    ResponsePrepCompensatingProductsOPTForm,
    ResponsePrepTemporaryExportedGoodsOPTForm,
    TemporaryExportedGoodsOPTForm,
)
from .models import (
    CP_CATEGORIES,
    OPTChecklist,
    OutwardProcessingTradeApplication,
    OutwardProcessingTradeFile,
)
from .utils import get_fq_form, get_fq_page_name


@login_required
def edit_opt(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = EditOPTForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:opt:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditOPTForm(instance=application, initial={"contact": request.user})

        supporting_documents = application.documents.filter(
            is_active=True, file_type=OutwardProcessingTradeFile.Type.SUPPORTING_DOCUMENT
        )

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit",
            "supporting_documents": supporting_documents,
            "prev_link": reverse("import:opt:edit", kwargs={"application_pk": application_pk}),
        }

        return render(request, "web/domains/case/import/opt/edit.html", context)


@login_required
def edit_compensating_products(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = CompensatingProductsOPTForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:opt:edit-compensating-products",
                        kwargs={"application_pk": application_pk},
                    )
                )

        else:
            form = CompensatingProductsOPTForm(instance=application)

        category_descriptions = _get_compensating_products_category_descriptions()
        category_label = category_descriptions.get(application.cp_category, "")

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit Compensating Products",
            "category_descriptions": category_descriptions,
            "category_label": category_label,
        }

        return render(
            request, "web/domains/case/import/opt/edit-compensating-products.html", context
        )


@login_required
def edit_temporary_exported_goods(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = TemporaryExportedGoodsOPTForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:opt:edit-temporary-exported-goods",
                        kwargs={"application_pk": application_pk},
                    )
                )

        else:
            form = TemporaryExportedGoodsOPTForm(instance=application)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit Temporary Exported Goods",
        }

        return render(
            request, "web/domains/case/import/opt/edit-temporary-exported-goods.html", context
        )


@login_required
def edit_further_questions(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = FurtherQuestionsOPTForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:opt:edit-further-questions",
                        kwargs={"application_pk": application_pk},
                    )
                )

        else:
            form = FurtherQuestionsOPTForm(instance=application)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit Further Questions",
        }

        return render(request, "web/domains/case/import/opt/edit-further-questions.html", context)


@login_required
def edit_further_questions_shared(
    request: AuthenticatedHttpRequest, *, application_pk: int, fq_type: str
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        form_class = get_fq_form(fq_type)

        if request.POST:
            has_files = application.documents.filter(is_active=True, file_type=fq_type).exists()

            form = form_class(data=request.POST, instance=application, has_files=has_files)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:opt:edit-further-questions-shared",
                        kwargs={"application_pk": application_pk, "fq_type": fq_type},
                    )
                )

        else:
            # no validation done on GETs, so pass in dummy has_files
            form = form_class(instance=application, has_files=False)

        supporting_documents = application.documents.filter(is_active=True, file_type=fq_type)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit Further Questions",
            "supporting_documents": supporting_documents,
            "file_type": fq_type,
            "fq_page_name": get_fq_page_name(fq_type),
        }

        return render(
            request, "web/domains/case/import/opt/edit-further-questions-shared.html", context
        )


@login_required
def submit_opt(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        errors = ApplicationErrors()

        edit_errors = PageErrors(
            page_name="Application details",
            url=reverse("import:opt:edit", kwargs={"application_pk": application_pk}),
        )
        create_page_errors(
            EditOPTForm(data=model_to_dict(application), instance=application), edit_errors
        )
        errors.add(edit_errors)

        cp_errors = PageErrors(
            page_name="Compensating Products",
            url=reverse(
                "import:opt:edit-compensating-products", kwargs={"application_pk": application_pk}
            ),
        )
        create_page_errors(
            CompensatingProductsOPTForm(data=model_to_dict(application), instance=application),
            cp_errors,
        )
        errors.add(cp_errors)

        teg_errors = PageErrors(
            page_name="Temporary Exported Goods",
            url=reverse(
                "import:opt:edit-temporary-exported-goods",
                kwargs={"application_pk": application_pk},
            ),
        )
        create_page_errors(
            TemporaryExportedGoodsOPTForm(data=model_to_dict(application), instance=application),
            teg_errors,
        )
        errors.add(teg_errors)

        fq_errors = PageErrors(
            page_name="Further Questions",
            url=reverse(
                "import:opt:edit-further-questions", kwargs={"application_pk": application_pk}
            ),
        )
        create_page_errors(
            FurtherQuestionsOPTForm(data=model_to_dict(application), instance=application),
            fq_errors,
        )
        errors.add(fq_errors)

        for file_type in OutwardProcessingTradeFile.Type.values:
            if not file_type.startswith("fq_"):
                continue

            form_class = get_fq_form(file_type)
            page_name = "Further Questions - " + get_fq_page_name(file_type)
            has_files = application.documents.filter(is_active=True, file_type=file_type).exists()

            fq_shared_errors = PageErrors(
                page_name=page_name, url=_get_edit_url(application_pk, file_type)
            )

            create_page_errors(
                form_class(
                    data=model_to_dict(application), instance=application, has_files=has_files
                ),
                fq_shared_errors,
            )

            errors.add(fq_shared_errors)

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                group = CommodityGroup.objects.get(
                    commodity_type__type_code="TEXTILES", group_code=application.cp_category
                )
                application.cp_category_licence_description = group.group_description
                application.submit_application(request, task)

                return application.redirect_after_submit(request)

        else:
            form = SubmitForm()

        declaration = Template.objects.filter(
            is_active=True,
            template_type=Template.DECLARATION,
            application_domain=Template.IMPORT_APPLICATION,
            template_code="IMA_OPT_DECLARATION",
        ).first()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Submit",
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/import/opt/submit.html", context)


def _get_edit_url(application_pk: int, file_type: str) -> str:
    """Get edit URL to the page responsible for editing the given filetype."""

    if file_type not in OutwardProcessingTradeFile.Type:  # type: ignore[operator]
        raise ValueError(f"Invalid file_type {file_type}")

    kwargs: dict[str, Any] = {"application_pk": application_pk}

    if file_type == OutwardProcessingTradeFile.Type.SUPPORTING_DOCUMENT:
        return reverse("import:opt:edit", kwargs=kwargs)

    else:
        return reverse(
            "import:opt:edit-further-questions-shared", kwargs=kwargs | {"fq_type": file_type}
        )


@login_required
def add_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, file_type: str
) -> HttpResponse:
    prev_link = _get_edit_url(application_pk, file_type)

    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")

                create_file_model(
                    document,
                    request.user,
                    application.documents,
                    extra_args={"file_type": file_type},
                )

                return redirect(prev_link)
        else:
            form = DocumentForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Outward Processing Trade Licence - Add supporting document",
            "prev_link": prev_link,
        }

        return render(request, "web/domains/case/import/opt/add_supporting_document.html", context)


@require_GET
@login_required
def view_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: OutwardProcessingTradeApplication = get_object_or_404(
        OutwardProcessingTradeApplication, pk=application_pk
    )

    return view_application_file(
        request.user, application, application.documents, document_pk, "import"
    )


@require_POST
@login_required
def delete_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        document = application.documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        edit_link = _get_edit_url(application_pk, document.file_type)

        return redirect(edit_link)


def _get_compensating_products_category_descriptions() -> dict[str, str]:
    groups = CommodityGroup.objects.filter(
        commodity_type__type_code="TEXTILES", group_code__in=CP_CATEGORIES
    )

    return {cg.group_code: cg.group_description for cg in groups}


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(ImportApplication.Statuses.SUBMITTED, "process")
        checklist, created = OPTChecklist.objects.get_or_create(import_application=application)

        if request.POST:
            form: OPTChecklistForm = OPTChecklistOptionalForm(request.POST, instance=checklist)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:opt:manage-checklist", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            if created:
                form = OPTChecklistForm(instance=checklist)
            else:
                form = OPTChecklistForm(data=model_to_dict(checklist), instance=checklist)

        context = {
            "process": application,
            "task": task,
            "page_title": "Outward Processing Trade Licence - Checklist",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def response_preparation_edit_compensating_products(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        task = application.get_task(ImportApplication.Statuses.SUBMITTED, "process")

        if request.POST:
            form = ResponsePrepCompensatingProductsOPTForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )

        else:
            form = ResponsePrepCompensatingProductsOPTForm(instance=application)

        context = {
            "process": application,
            "task": task,
            "form": form,
            "case_type": "import",
            "page_title": "Outward Processing Trade Import Licence - Edit Compensating Products",
        }

        return render(
            request, "web/domains/case/import/manage/response-prep-edit-form.html", context
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def response_preparation_edit_temporary_exported_goods(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        task = application.get_task(ImportApplication.Statuses.SUBMITTED, "process")

        if request.POST:
            form = ResponsePrepTemporaryExportedGoodsOPTForm(
                data=request.POST, instance=application
            )

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )

        else:
            form = ResponsePrepTemporaryExportedGoodsOPTForm(instance=application)

        context = {
            "process": application,
            "task": task,
            "form": form,
            "case_type": "import",
            "page_title": "Outward Processing Trade Import Licence - Edit Temporary Exported Goods",
        }

        return render(
            request, "web/domains/case/import/manage/response-prep-edit-form.html", context
        )
