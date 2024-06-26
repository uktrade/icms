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
from web.domains.case.views.utils import get_caseworker_view_readonly_status
from web.domains.file.utils import create_file_model
from web.domains.template.utils import add_template_data_on_submit
from web.models import Country, Task, User
from web.permissions import AppChecker, Perms
from web.types import AuthenticatedHttpRequest
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .forms import (
    DerogationsChecklistForm,
    DerogationsChecklistOptionalForm,
    DerogationsSyriaChecklistForm,
    DerogationsSyriaChecklistOptionalForm,
    EditDerogationsForm,
    GoodsDerogationsLicenceForm,
    SubmitDerogationsForm,
)
from .models import DerogationsApplication, DerogationsChecklist


def check_can_edit_application(user: User, application: DerogationsApplication) -> None:
    checker = AppChecker(user, application)

    if not checker.can_edit():
        raise PermissionDenied


@login_required
def edit_derogations(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        syria = Country.objects.get(name="Syria")

        form = get_application_form(
            application, request, EditDerogationsForm, SubmitDerogationsForm
        )

        if request.method == "POST":
            if form.is_valid():
                application = form.save(commit=False)

                # Clear the syria section if needed
                if syria not in (application.origin_country, application.consignment_country):
                    application.entity_consulted_name = None
                    application.activity_benefit_anyone = None
                    application.purpose_of_request = None
                    application.civilian_purpose_details = None

                application.save()
                messages.success(request, "Application data saved")

                return redirect(
                    reverse("import:derogations:edit", kwargs={"application_pk": application_pk})
                )

        supporting_documents = application.supporting_documents.filter(is_active=True)

        show_fd = syria in (application.origin_country, application.consignment_country)

        context = {
            "process": application,
            "form": form,
            "page_title": get_page_title("Edit"),
            "supporting_documents": supporting_documents,
            "show_further_details": show_fd,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/derogations/edit.html", context)


@login_required
def add_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, application.supporting_documents)

                return redirect(
                    reverse("import:derogations:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DocumentForm()

        context = {
            "process": application,
            "form": form,
            "page_title": get_page_title("Add supporting document"),
            "case_type": "import",
        }

        return render(
            request, "web/domains/case/import/derogations/add_supporting_document.html", context
        )


@require_GET
@login_required
def view_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: DerogationsApplication = get_object_or_404(
        DerogationsApplication, pk=application_pk
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
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(
            reverse("import:derogations:edit", kwargs={"application_pk": application_pk})
        )


@login_required
def submit_derogations(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        check_can_edit_application(request.user, application)

        case_progress.application_in_progress(application)
        task = case_progress.get_expected_task(application, Task.TaskType.PREPARE)

        errors = _get_derogations_errors(application)

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
            "page_title": get_page_title("Submit"),
            "declaration": application.application_type.declaration_template,
            "errors": errors if errors.has_errors() else None,
            "case_type": "import",
        }

        return render(request, "web/domains/case/import/import-case-submit.html", context)


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )
        readonly_view = get_caseworker_view_readonly_status(application, "import", request.user)

        checklist, created = DerogationsChecklist.objects.get_or_create(
            import_application=application
        )

        syria = Country.objects.get(name="Syria")
        include_extra = syria in (application.origin_country, application.consignment_country)

        if include_extra:
            checklist_form = DerogationsSyriaChecklistForm
            checklist_optional_form = DerogationsSyriaChecklistOptionalForm
        else:
            checklist_form = DerogationsChecklistForm
            checklist_optional_form = DerogationsChecklistOptionalForm

        if request.method == "POST" and not readonly_view:
            form: DerogationsChecklistForm = checklist_optional_form(
                request.POST, instance=checklist
            )

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:derogations:manage-checklist",
                        kwargs={"application_pk": application_pk},
                    )
                )
        else:
            if created:
                form = checklist_form(instance=checklist, readonly_form=readonly_view)
            else:
                form = checklist_form(
                    data=model_to_dict(checklist), instance=checklist, readonly_form=readonly_view
                )

        context = {
            "process": application,
            "page_title": get_page_title("Checklist"),
            "form": form,
            "readonly_view": readonly_view,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )


@login_required
@permission_required(Perms.sys.ilb_admin, raise_exception=True)
def edit_goods_licence(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        case_progress.application_in_processing(application)

        if request.method == "POST":
            form = GoodsDerogationsLicenceForm(request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "case:prepare-response",
                        kwargs={"application_pk": application_pk, "case_type": "import"},
                    )
                )
        else:
            form = GoodsDerogationsLicenceForm(instance=application)

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


def get_page_title(page: str) -> str:
    return f"Derogation from Sanctions Import Ban - {page}"


def _get_derogations_errors(application: DerogationsApplication) -> ApplicationErrors:
    errors = ApplicationErrors()

    edit_url = reverse("import:derogations:edit", kwargs={"application_pk": application.pk})
    edit_url = f"{edit_url}?validate"

    page_errors = PageErrors(page_name="Application Details", url=edit_url)
    create_page_errors(
        SubmitDerogationsForm(data=model_to_dict(application), instance=application), page_errors
    )
    errors.add(page_errors)

    if not application.supporting_documents.filter(is_active=True).exists():
        supporting_document_errors = PageErrors(
            page_name="Supporting Documents",
            url=reverse(
                "import:derogations:add-supporting-document",
                kwargs={"application_pk": application.pk},
            ),
        )
        supporting_document_errors.add(
            FieldError(
                field_name="Provide details of why this is a pre-existing contract",
                messages=["Please ensure you have uploaded at least one supporting document."],
            )
        )

        errors.add(supporting_document_errors)

    errors.add(get_org_update_request_errors(application, "import"))

    return errors
