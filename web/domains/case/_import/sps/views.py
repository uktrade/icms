from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplication
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.views import (
    check_application_permission,
    view_application_file,
    view_application_file_direct,
)
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.types import AuthenticatedHttpRequest
from web.utils.currency import convert_gbp_to_euro
from web.utils.validation import (
    ApplicationErrors,
    FieldError,
    PageErrors,
    create_page_errors,
)

from .forms import AddContractDocumentForm, EditContractDocumentForm, EditSPSForm
from .models import PriorSurveillanceApplication, PriorSurveillanceContractFile


@login_required
def edit_sps(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = EditSPSForm(data=request.POST, instance=application)

            if form.is_valid():
                instance: PriorSurveillanceApplication = form.save(commit=False)
                instance.value_euro = convert_gbp_to_euro(instance.value_gbp)
                instance.save()

                return redirect(
                    reverse("import:sps:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditSPSForm(instance=application, initial={"contact": request.user})

        supporting_documents = application.supporting_documents.filter(is_active=True)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Prior Surveillance Import Licence - Edit",
            "supporting_documents": supporting_documents,
        }

        return render(request, "web/domains/case/import/sps/edit.html", context)


@login_required
def submit_sps(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        errors = ApplicationErrors()

        edit_errors = PageErrors(
            page_name="Application details",
            url=reverse("import:sps:edit", kwargs={"application_pk": application_pk}),
        )
        create_page_errors(
            EditSPSForm(data=model_to_dict(application), instance=application), edit_errors
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

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                application.submit_application(request, task)

                return application.redirect_after_submit(request)

        else:
            form = SubmitForm()

        declaration = Template.objects.filter(
            is_active=True,
            template_type=Template.DECLARATION,
            application_domain=Template.IMPORT_APPLICATION,
            template_code="IMA_SPS_DECLARATION",
        ).first()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Prior Surveillance Import Licence - Submit",
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/import/sps/submit.html", context)


@login_required
def add_supporting_document(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: PriorSurveillanceApplication = get_object_or_404(
            PriorSurveillanceApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
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
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Prior Surveillance Import Licence - Add supporting document",
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
        request.user, application, application.supporting_documents, document_pk, "import"
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

        check_application_permission(application, request.user, "import")

        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

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

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
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
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Prior Surveillance Import Licence - Add contract document",
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

    return view_application_file_direct(
        request.user, application, application.contract_file, "import"
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

        check_application_permission(application, request.user, "import")

        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

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

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        document = application.contract_file

        if request.POST:
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
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Prior Surveillance Import Licence - Edit contract document",
        }

        return render(request, "web/domains/case/import/sps/edit_contract_document.html", context)
