from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import ModelForm, model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.utils import (
    check_application_permission,
    get_application_current_task,
    get_application_form,
    redirect_after_submit,
    submit_application,
    view_application_file,
)
from web.domains.case.views.utils import get_current_task_and_readonly_status
from web.domains.commodity.models import CommodityGroup
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .forms import (
    EditCompensatingProductsOPTForm,
    EditFurtherQuestionsOPTForm,
    EditOPTForm,
    EditTemporaryExportedGoodsOPTForm,
    OPTChecklistForm,
    OPTChecklistOptionalForm,
    ResponsePrepCompensatingProductsOPTForm,
    ResponsePrepTemporaryExportedGoodsOPTForm,
    SubmitCompensatingProductsOPTForm,
    SubmitFurtherQuestionsOPTForm,
    SubmitOptForm,
    SubmitTemporaryExportedGoodsOPTForm,
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

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        form = get_application_form(application, request, EditOPTForm, SubmitOptForm)

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("import:opt:edit", kwargs={"application_pk": application_pk})
                )

        supporting_documents = application.documents.filter(
            is_active=True, file_type=OutwardProcessingTradeFile.Type.SUPPORTING_DOCUMENT
        )

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit",
            "supporting_documents": supporting_documents,
            "prev_link": reverse("import:opt:edit", kwargs={"application_pk": application_pk}),
            "case_type": "import",
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

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        form = _get_opt_form_instance(
            application, request, EditCompensatingProductsOPTForm, SubmitCompensatingProductsOPTForm
        )

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse(
                        "import:opt:edit-compensating-products",
                        kwargs={"application_pk": application_pk},
                    )
                )

        category_descriptions = _get_compensating_products_category_descriptions()
        category_label = category_descriptions.get(application.cp_category, "")

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit Compensating Products",
            "category_descriptions": category_descriptions,
            "category_label": category_label,
            "case_type": "import",
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

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        form = _get_opt_form_instance(
            application,
            request,
            EditTemporaryExportedGoodsOPTForm,
            SubmitTemporaryExportedGoodsOPTForm,
        )

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse(
                        "import:opt:edit-temporary-exported-goods",
                        kwargs={"application_pk": application_pk},
                    )
                )

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit Temporary Exported Goods",
            "case_type": "import",
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

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        form = _get_opt_form_instance(
            application, request, EditFurtherQuestionsOPTForm, SubmitFurtherQuestionsOPTForm
        )

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse(
                        "import:opt:edit-further-questions",
                        kwargs={"application_pk": application_pk},
                    )
                )

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit Further Questions",
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/opt/edit-further-questions.html", context)


def _get_opt_form_instance(
    application: OutwardProcessingTradeApplication,
    request: AuthenticatedHttpRequest,
    edit_form: type[ModelForm],
    submit_form: type[ModelForm],
) -> ModelForm:
    """Create a form instance for one of several OPT forms."""

    if request.method == "POST":
        form = edit_form(data=request.POST, instance=application)
    else:
        form_kwargs = {"instance": application}

        if "validate" in request.GET:
            form_kwargs["data"] = model_to_dict(application)
            form = submit_form(**form_kwargs)
        else:
            form = edit_form(**form_kwargs)

    return form


@login_required
def edit_further_questions_shared(
    request: AuthenticatedHttpRequest, *, application_pk: int, fq_type: str
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        form_class = get_fq_form(fq_type)

        if request.method == "POST":
            has_files = application.documents.filter(is_active=True, file_type=fq_type).exists()

            form = form_class(data=request.POST, instance=application, has_files=has_files)

            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

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
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit Further Questions",
            "supporting_documents": supporting_documents,
            "file_type": fq_type,
            "fq_page_name": get_fq_page_name(fq_type),
            "case_type": "import",
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

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        errors = ApplicationErrors()

        app_kwargs = {"application_pk": application_pk}
        app_data = model_to_dict(application)

        edit_url = reverse("import:opt:edit", kwargs=app_kwargs)
        edit_url = f"{edit_url}?validate"

        edit_errors = PageErrors(page_name="Application details", url=edit_url)
        create_page_errors(SubmitOptForm(data=app_data, instance=application), edit_errors)
        errors.add(edit_errors)

        comp_prod_url = reverse("import:opt:edit-compensating-products", kwargs=app_kwargs)
        comp_prod_url = f"{comp_prod_url}?validate"

        cp_errors = PageErrors(page_name="Compensating Products", url=comp_prod_url)
        create_page_errors(
            SubmitCompensatingProductsOPTForm(data=app_data, instance=application),
            cp_errors,
        )
        errors.add(cp_errors)

        exp_goods_url = reverse("import:opt:edit-temporary-exported-goods", kwargs=app_kwargs)
        exp_goods_url = f"{exp_goods_url}?validate"

        teg_errors = PageErrors(page_name="Temporary Exported Goods", url=exp_goods_url)
        create_page_errors(
            SubmitTemporaryExportedGoodsOPTForm(data=app_data, instance=application),
            teg_errors,
        )
        errors.add(teg_errors)

        further_qs_url = reverse("import:opt:edit-further-questions", kwargs=app_kwargs)
        further_qs_url = f"{further_qs_url}?validate"

        fq_errors = PageErrors(page_name="Further Questions", url=further_qs_url)
        create_page_errors(
            SubmitFurtherQuestionsOPTForm(data=app_data, instance=application),
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
                form_class(data=app_data, instance=application, has_files=has_files),
                fq_shared_errors,
            )

            errors.add(fq_shared_errors)

        errors.add(get_org_update_request_errors(application, "import"))

        if request.method == "POST":
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                group = CommodityGroup.objects.get(
                    commodity_type__type_code="TEXTILES", group_code=application.cp_category
                )
                application.cp_category_licence_description = group.group_description
                submit_application(application, request, task)

                return redirect_after_submit(application, request)

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
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Submit",
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/import-case-submit.html", context)


def _get_edit_url(application_pk: int, file_type: str) -> str:
    """Get edit URL to the page responsible for editing the given filetype."""

    if file_type not in OutwardProcessingTradeFile.Type:  # type: ignore[attr-defined]
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

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        if request.method == "POST":
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
            "form": form,
            "page_title": "Outward Processing Trade Licence - Add supporting document",
            "prev_link": prev_link,
            "case_type": "import",
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

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

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
@permission_required("web.ilb_admin", raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )
        _, readonly_view = get_current_task_and_readonly_status(
            application, "import", request.user, Task.TaskType.PROCESS
        )

        checklist, created = OPTChecklist.objects.get_or_create(import_application=application)

        if request.method == "POST" and not readonly_view:
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
                form = OPTChecklistForm(instance=checklist, readonly_form=readonly_view)
            else:
                form = OPTChecklistForm(
                    data=model_to_dict(checklist), instance=checklist, readonly_form=readonly_view
                )

        context = {
            "process": application,
            "page_title": "Outward Processing Trade Licence - Checklist",
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
def response_preparation_edit_compensating_products(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, "import", Task.TaskType.PROCESS)

        if request.method == "POST":
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
            "form": form,
            "case_type": "import",
            "page_title": "Outward Processing Trade Import Licence - Edit Compensating Products",
        }

        return render(
            request, "web/domains/case/import/manage/response-prep-edit-form.html", context
        )


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def response_preparation_edit_temporary_exported_goods(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        get_application_current_task(application, "import", Task.TaskType.PROCESS)

        if request.method == "POST":
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
            "form": form,
            "case_type": "import",
            "page_title": "Outward Processing Trade Import Licence - Edit Temporary Exported Goods",
        }

        return render(
            request, "web/domains/case/import/manage/response-prep-edit-form.html", context
        )
