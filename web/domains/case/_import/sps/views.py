from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplication
from web.domains.case.forms import DocumentForm, SubmitForm
from web.domains.case.views import check_application_permission, view_application_file
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.types import AuthenticatedHttpRequest
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .forms import EditSPSForm
from .models import PriorSurveillanceApplication


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
                form.save()

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

        if request.POST:
            form = SubmitForm(data=request.POST)

            if form.is_valid() and not errors.has_errors():
                application.submit_application(request, task)

                return redirect(reverse("workbasket"))

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
def add_document(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
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
def view_document(
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
def delete_document(
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
