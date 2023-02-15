from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from storages.backends.s3boto3 import S3Boto3StorageFile

from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.services import case_progress
from web.domains.case.utils import (
    check_application_permission,
    get_application_form,
    redirect_after_submit,
    submit_application,
)
from web.domains.case.views.utils import get_caseworker_view_readonly_status
from web.domains.file.utils import create_file_model
from web.domains.template.utils import add_template_data_on_submit
from web.flow.models import Task
from web.types import AuthenticatedHttpRequest
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .. import views as import_views
from .forms import (
    AddContractDocumentForm,
    EditContractDocumentForm,
    EditWoodQuotaForm,
    GoodsWoodQuotaLicenceForm,
    SubmitWoodQuotaForm,
    WoodQuotaChecklistForm,
    WoodQuotaChecklistOptionalForm,
)
from .models import WoodQuotaApplication, WoodQuotaChecklist


@login_required
def edit_wood_quota(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: WoodQuotaApplication = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        form = get_application_form(application, request, EditWoodQuotaForm, SubmitWoodQuotaForm)

        if request.method == "POST":
            if form.is_valid():
                form.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("import:wood:edit", kwargs={"application_pk": application_pk})
                )

        supporting_documents = application.supporting_documents.filter(is_active=True)
        contract_documents = application.contract_documents.filter(is_active=True)

        context = {
            "process": application,
            "form": form,
            "page_title": "Wood (Quota) Import Licence - Edit",
            "supporting_documents": supporting_documents,
            "contract_documents": contract_documents,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/wood/edit.html", context)


@login_required
def add_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, application.supporting_documents)

                return redirect(
                    reverse("import:wood:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DocumentForm()

        context = {
            "process": application,
            "form": form,
            "page_title": "Wood (Quota) Import Licence - Add supporting document",
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/wood/add_supporting_document.html", context)


@require_GET
@login_required
def view_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application = get_object_or_404(WoodQuotaApplication, pk=application_pk)

    return import_views.view_file(
        request, application, application.supporting_documents, document_pk
    )


@require_POST
@login_required
def delete_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:wood:edit", kwargs={"application_pk": application_pk}))


@login_required
def add_contract_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: WoodQuotaApplication = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = AddContractDocumentForm(data=request.POST, files=request.FILES)

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
                    application.contract_documents,
                    extra_args=extra_args,
                )

                return redirect(
                    reverse("import:wood:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = AddContractDocumentForm()

        context = {
            "process": application,
            "form": form,
            "page_title": "Wood (Quota) Import Licence - Add contract document",
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/wood/add_contract_document.html", context)


@require_GET
@login_required
def view_contract_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application = get_object_or_404(WoodQuotaApplication, pk=application_pk)

    return import_views.view_file(request, application, application.contract_documents, document_pk)


@require_POST
@login_required
def delete_contract_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        document = application.contract_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:wood:edit", kwargs={"application_pk": application_pk}))


@login_required
def edit_contract_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        document = application.contract_documents.get(pk=document_pk)

        if request.method == "POST":
            form = EditContractDocumentForm(data=request.POST, instance=document)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:wood:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditContractDocumentForm(instance=document)

        context = {
            "process": application,
            "form": form,
            "page_title": "Wood (Quota) Import Licence - Edit contract document",
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/wood/edit_contract_document.html", context)


@login_required
def submit_wood_quota(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = ApplicationErrors()

        edit_url = reverse("import:wood:edit", kwargs={"application_pk": application_pk})
        edit_url = f"{edit_url}?validate"

        page_errors = PageErrors(page_name="Application details", url=edit_url)
        create_page_errors(
            SubmitWoodQuotaForm(data=model_to_dict(application), instance=application), page_errors
        )
        errors.add(page_errors)

        if not application.contract_documents.filter(is_active=True).exists():
            contract_document_errors = PageErrors(
                page_name="Add contract document",
                url=reverse(
                    "import:wood:add-contract-document", kwargs={"application_pk": application_pk}
                ),
            )

            contract_document_errors.add(
                FieldError(
                    field_name="Contract Document",
                    messages=["At least one contract document must be added"],
                )
            )

            errors.add(contract_document_errors)

        errors.add(get_org_update_request_errors(application, "import"))

        if request.method == "POST":
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                submit_application(application, request, task)
                add_template_data_on_submit(application)

                return redirect_after_submit(application, request)

        else:
            form = SubmitForm()

        context = {
            "process": application,
            "form": form,
            "page_title": "Wood (Quota) Import Licence - Submit",
            "declaration": application.application_type.declaration_template,
            "errors": errors if errors.has_errors() else None,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/import-case-submit.html", context)


@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: WoodQuotaApplication = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )
        readonly_view = get_caseworker_view_readonly_status(application, "import", request.user)
        checklist, created = WoodQuotaChecklist.objects.get_or_create(
            import_application=application
        )

        if request.method == "POST" and not readonly_view:
            form: WoodQuotaChecklistForm = WoodQuotaChecklistOptionalForm(
                request.POST, instance=checklist
            )

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:wood:manage-checklist", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            if created:
                form = WoodQuotaChecklistForm(instance=checklist, readonly_form=readonly_view)
            else:
                form = WoodQuotaChecklistForm(
                    data=model_to_dict(checklist), instance=checklist, readonly_form=readonly_view
                )

        context = {
            "process": application,
            "page_title": "Wood (Quota) Import Licence - Checklist",
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
def edit_goods(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: WoodQuotaApplication = get_object_or_404(
            WoodQuotaApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        if request.method == "POST":
            form = GoodsWoodQuotaLicenceForm(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application.pk, "case_type": "import"},
                    )
                )
        else:
            form = GoodsWoodQuotaLicenceForm(instance=application)

        context = {
            "case_type": "import",
            "process": application,
            "page_title": "Edit Goods",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/manage/response-prep-edit-form.html",
            context=context,
        )
