from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case.app_checks import get_org_update_request_errors
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.services import case_progress
from web.domains.case.utils import (
    get_application_form,
    redirect_after_submit,
    submit_application,
    view_application_file,
)
from web.domains.file.utils import create_file_model
from web.domains.template.utils import add_template_data_on_submit
from web.models import (
    PriorSurveillanceApplication,
    PriorSurveillanceContractFile,
    Task,
    User,
)
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest
from web.utils.currency import convert_gbp_to_euro
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .forms import (
    AddContractDocumentForm,
    EditContractDocumentForm,
    EditSPSForm,
    ResponsePrepGoodsForm,
    SubmitSPSForm,
)


def check_can_edit_application(user: User, application: PriorSurveillanceApplication) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


@login_required
def edit_sps(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        form = get_application_form(application, request, EditSPSForm, SubmitSPSForm)

        if request.method == "POST":
            if form.is_valid():
                instance: PriorSurveillanceApplication = form.save(commit=False)

                if instance.value_gbp:
                    instance.value_eur = convert_gbp_to_euro(instance.value_gbp)

                instance.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("import:sps:edit", kwargs={"application_pk": application_pk})
                )

        supporting_documents = application.supporting_documents.filter(is_active=True)

        context = {
            "process": application,
            "form": form,
            "page_title": "Prior Surveillance Import Licence - Edit",
            "supporting_documents": supporting_documents,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/sps/edit.html", context)


@login_required
def submit_sps(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = ApplicationErrors()

        edit_url = reverse("import:sps:edit", kwargs={"application_pk": application.pk})
        edit_url = f"{edit_url}?validate"

        edit_errors = PageErrors(page_name="Application Details", url=edit_url)
        create_page_errors(
            SubmitSPSForm(data=model_to_dict(application), instance=application), edit_errors
        )

        errors.add(edit_errors)

        if not application.contract_file:
            contract_errors = PageErrors(
                page_name="Add contract/invoice document",
                url=reverse(
                    "import:sps:add-contract-document", kwargs={"application_pk": application_pk}
                ),
            )

            contract_errors.add(
                FieldError(field_name="Certificates/Documents", messages=["You must upload a file"])
            )

            errors.add(contract_errors)

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
            "page_title": "Prior Surveillance Import Licence - Submit",
            "declaration": application.application_type.declaration_template,
            "errors": errors if errors.has_errors() else None,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/import-case-submit.html", context)


@login_required
def add_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, application.supporting_documents)

                return redirect(
                    reverse("import:sps:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DocumentForm()

        context = {
            "process": application,
            "form": form,
            "page_title": "Prior Surveillance Import Licence - Add supporting document",
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/sps/add_supporting_document.html", context)


@require_GET
@login_required
def view_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: PriorSurveillanceApplication = get_object_or_404(
        PriorSurveillanceApplication, pk=application_pk
    )

    return view_application_file(
        request.user, application, application.supporting_documents, document_pk
    )


@require_POST
@login_required
def delete_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:sps:edit", kwargs={"application_pk": application_pk}))


@login_required
def add_contract_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = AddContractDocumentForm(data=request.POST, files=request.FILES)

            if application.contract_file:
                form.add_error("document", "Application already has a contract/invoice uploaded")

            elif form.is_valid():
                document = form.cleaned_data.get("document")

                extra_args = {
                    field: value
                    for (field, value) in form.cleaned_data.items()
                    if field not in ["document"]
                }

                file_model = create_file_model(
                    document,
                    request.user,
                    PriorSurveillanceContractFile.objects,
                    extra_args=extra_args,
                )

                application.contract_file = file_model
                application.save()

                return redirect(
                    reverse("import:sps:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = AddContractDocumentForm()

        context = {
            "process": application,
            "form": form,
            "page_title": "Prior Surveillance Import Licence - Add contract document",
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/sps/add_contract_document.html", context)


@require_GET
@login_required
def view_contract_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    application: PriorSurveillanceApplication = get_object_or_404(
        PriorSurveillanceApplication, pk=application_pk
    )

    if not application.contract_file:
        messages.error(request, "The application does not have contract/invoice attached.")

        return redirect(reverse("import:sps:edit", kwargs={"application_pk": application_pk}))

    return view_application_file(
        request.user,
        application,
        PriorSurveillanceContractFile.objects,
        application.contract_file_id,
    )


@require_POST
@login_required
def delete_contract_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        if application.contract_file:
            file_model = application.contract_file

            application.contract_file = None
            application.save()

            file_model.delete()
        else:
            messages.error(request, "The application does not have contract/invoice attached.")

        return redirect(reverse("import:sps:edit", kwargs={"application_pk": application_pk}))


@login_required
def edit_contract_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        document = application.contract_file

        if request.method == "POST":
            form = EditContractDocumentForm(data=request.POST, instance=document)

            if not document:
                form.add_error("file_type", "Application does not have a contract/invoice uploaded")

            elif form.is_valid():
                form.save()

                return redirect(
                    reverse("import:sps:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditContractDocumentForm(instance=document)

        context = {
            "process": application,
            "form": form,
            "page_title": "Prior Surveillance Import Licence - Edit contract document",
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/sps/edit_contract_document.html", context)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def response_preparation_edit_goods(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        if request.method == "POST":
            form = ResponsePrepGoodsForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )

        else:
            form = ResponsePrepGoodsForm(instance=application)

        context = {
            "process": application,
            "form": form,
            "case_type": "import",
            "page_title": "Prior Surveillance Import Licence - Edit Goods",
        }

        return render(
            request, "web/domains/case/import/manage/response-prep-edit-form.html", context
        )
