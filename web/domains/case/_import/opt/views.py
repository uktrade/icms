from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplication
from web.domains.case.forms import DocumentForm
from web.domains.case.views import check_application_permission, view_application_file
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.flow.models import Task
from web.utils.validation import ApplicationErrors, PageErrors, create_page_errors

from .forms import (
    CompensatingProductsOPTForm,
    EditOPTForm,
    FurtherQuestionsOPTForm,
    SubmitOPTForm,
)
from .models import OutwardProcessingTradeApplication


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_opt(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        # TODO: use check_application_permission
        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = EditOPTForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:opt:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditOPTForm(instance=application, initial={"contact": request.user})

        supporting_documents = application.supporting_documents.filter(is_active=True)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit",
            "supporting_documents": supporting_documents,
        }

        return render(request, "web/domains/case/import/opt/edit.html", context)


@login_required
def edit_compensating_products(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

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

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Outward Processing Trade Import Licence - Edit Compensating Products",
        }

        return render(
            request, "web/domains/case/import/opt/edit-compensating-products.html", context
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_further_questions(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        # TODO: use check_application_permission
        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

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
@permission_required("web.importer_access", raise_exception=True)
def submit_opt(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        # TODO: use check_application_permission
        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        errors = ApplicationErrors()

        edit_errors = PageErrors(
            page_name="Application details",
            url=reverse("import:opt:edit", kwargs={"application_pk": application_pk}),
        )
        create_page_errors(
            EditOPTForm(data=model_to_dict(application), instance=application), edit_errors
        )
        errors.add(edit_errors)

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

        if request.POST:
            form = SubmitOPTForm(data=request.POST)

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
            form = SubmitOPTForm()

        # TODO: ICMSLST-599 what template to use?
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
            "page_title": "Outward Processing Trade Import Licence - Submit",
            "declaration": declaration,
            "errors": errors if errors.has_errors() else None,
        }

        return render(request, "web/domains/case/import/opt/submit.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def add_supporting_document(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        # TODO: use check_application_permission
        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = DocumentForm(data=request.POST, files=request.FILES)
            document = request.FILES.get("document")

            if form.is_valid():
                create_file_model(document, request.user, application.supporting_documents)

                return redirect(
                    reverse("import:opt:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DocumentForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Outward Processing Trade Licence - Add supporting document",
        }

        return render(request, "web/domains/case/import/opt/add_supporting_document.html", context)


@require_GET
@login_required
def view_supporting_document(
    request: HttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: OutwardProcessingTradeApplication = get_object_or_404(
        OutwardProcessingTradeApplication, pk=application_pk
    )

    return view_application_file(
        request.user, application, application.supporting_documents, document_pk, "import"
    )


@require_POST
@login_required
@permission_required("web.importer_access", raise_exception=True)
def delete_supporting_document(
    request: HttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: OutwardProcessingTradeApplication = get_object_or_404(
            OutwardProcessingTradeApplication.objects.select_for_update(), pk=application_pk
        )

        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        # TODO: use check_application_permission
        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:opt:edit", kwargs={"application_pk": application_pk}))
