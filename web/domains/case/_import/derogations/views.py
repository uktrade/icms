from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplication
from web.domains.file.views import handle_uploaded_file
from web.domains.template.models import Template
from web.flow.models import Task
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .. import views as import_views
from .forms import DerogationsForm, SubmitDerogationsForm, SupportingDocumentForm
from .models import DerogationsApplication


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_derogations(request, pk):
    with transaction.atomic():
        application = get_object_or_404(DerogationsApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.method == "POST":
            form = DerogationsForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(reverse("import:derogations:edit-derogations", kwargs={"pk": pk}))
        else:
            form = DerogationsForm(instance=application, initial={"contact": request.user})

        # TODO: after ICMSLST-602 is done, we'll know whether we need to filter
        # by error_message being None or not
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
def add_supporting_document(request: HttpRequest, pk: int) -> HttpResponse:

    with transaction.atomic():
        application = get_object_or_404(DerogationsApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = SupportingDocumentForm(data=request.POST, files=request.FILES)
            document = request.FILES.get("document")

            if form.is_valid():
                handle_uploaded_file(document, request.user, application.supporting_documents)

                return redirect(reverse("import:derogations:edit-derogations", kwargs={"pk": pk}))
        else:
            form = SupportingDocumentForm()

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
    request: HttpRequest, application_pk: int, document_pk: int
) -> HttpResponse:
    application = get_object_or_404(DerogationsApplication, pk=application_pk)

    return import_views._view_file(
        request, application, application.supporting_documents, document_pk
    )


@require_POST
@login_required
@permission_required("web.importer_access", raise_exception=True)
def delete_supporting_document(
    request: HttpRequest, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            DerogationsApplication.objects.select_for_update(), pk=application_pk
        )

        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(
            reverse("import:derogations:edit-derogations", kwargs={"pk": application_pk})
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def submit_derogations(request, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(DerogationsApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        errors = ApplicationErrors()

        page_errors = PageErrors(
            page_name="Application details",
            url=reverse("import:derogations:edit-derogations", kwargs={"pk": pk}),
        )
        create_page_errors(
            DerogationsForm(data=model_to_dict(application), instance=application), page_errors
        )
        errors.add(page_errors)

        if request.POST:
            form = SubmitDerogationsForm(data=request.POST)

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
            form = SubmitDerogationsForm()

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


def get_page_title(page: str) -> str:
    return f"Derogation from Sanctions Import Ban - {page}"
