from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplication
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.types import AuthenticatedHttpRequest
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .. import views as import_views
from .forms import (
    DerogationsChecklistForm,
    DerogationsChecklistOptionalForm,
    DerogationsForm,
    GoodsDerogationsLicenceForm,
)
from .models import DerogationsApplication, DerogationsChecklist


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_derogations(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.method == "POST":
            form = DerogationsForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:derogations:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DerogationsForm(instance=application, initial={"contact": request.user})

        supporting_documents = application.supporting_documents.filter(is_active=True)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": get_page_title("Edit"),
            "supporting_documents": supporting_documents,
        }

        return render(request, "web/domains/case/import/derogations/edit.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def add_supporting_document(request: AuthenticatedHttpRequest, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
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
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": get_page_title("Add supporting document"),
        }

        return render(
            request, "web/domains/case/import/derogations/add_supporting_document.html", context
        )


@require_GET
@login_required
def view_supporting_document(
    request: AuthenticatedHttpRequest, application_pk: int, document_pk: int
) -> HttpResponse:
    application: DerogationsApplication = get_object_or_404(
        DerogationsApplication, pk=application_pk
    )

    return import_views.view_file(
        request, application, application.supporting_documents, document_pk
    )


@require_POST
@login_required
@permission_required("web.importer_access", raise_exception=True)
def delete_supporting_document(
    request: AuthenticatedHttpRequest, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(
            reverse("import:derogations:edit", kwargs={"application_pk": application_pk})
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def submit_derogations(request: AuthenticatedHttpRequest, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        errors = _get_derogations_errors(application)

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                application.submit_application(request, task)

                # TODO: replace with Endorsement Usage Template (ICMSLST-638)
                # endorsements are active on ICMS1 but inactive in our db
                # first_endorsement = Template.objects.get(
                #     is_active=True,
                #     template_type=Template.ENDORSEMENT,
                #     template_name="Endorsement 1 (must be updated each year)",
                # )
                # application.endorsements.create(content=first_endorsement.template_content)
                # second_endorsement = Template.objects.get(
                #     is_active=True,
                #     template_type=Template.ENDORSEMENT,
                #     template_name="Endorsement 15",
                # )
                # application.endorsements.create(content=second_endorsement.template_content)

                return redirect(reverse("home"))

        else:
            form = SubmitForm()

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
            "form": form,
            "page_title": get_page_title("Submit"),
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/import/derogations/submit.html", context)


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_checklist(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(ImportApplication.Statuses.SUBMITTED, "process")
        checklist, created = DerogationsChecklist.objects.get_or_create(
            import_application=application
        )

        if request.POST:
            form: DerogationsChecklistForm = DerogationsChecklistOptionalForm(
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
                form = DerogationsChecklistForm(instance=checklist)
            else:
                form = DerogationsChecklistForm(data=model_to_dict(checklist), instance=checklist)

        context = {
            "process": application,
            "task": task,
            "page_title": get_page_title("Checklist"),
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_goods_licence(request: AuthenticatedHttpRequest, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: DerogationsApplication = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )
        task = application.get_task(
            [ImportApplication.Statuses.SUBMITTED, ImportApplication.Statuses.WITHDRAWN], "process"
        )

        if request.POST:
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
            "task": task,
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

    page_errors = PageErrors(
        page_name="Application details",
        url=reverse("import:derogations:edit", kwargs={"application_pk": application.pk}),
    )
    create_page_errors(
        DerogationsForm(data=model_to_dict(application), instance=application), page_errors
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

    return errors
