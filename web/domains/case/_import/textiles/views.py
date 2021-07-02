from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.models import ImportApplication
from web.domains.case.forms import DocumentForm
from web.domains.case.views import check_application_permission, view_application_file
from web.domains.file.utils import create_file_model
from web.types import AuthenticatedHttpRequest

from .forms import EditTextilesForm
from .models import TextilesApplication


@login_required
def edit_textiles(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = EditTextilesForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:textiles:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditTextilesForm(instance=application, initial={"contact": request.user})

        supporting_documents = application.supporting_documents.filter(is_active=True)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Textiles (Quota) Import Licence - Edit",
            "supporting_documents": supporting_documents,
        }

        return render(request, "web/domains/case/import/textiles/edit.html", context)


@login_required
def add_document(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, application.supporting_documents)

                return redirect(
                    reverse("import:textiles:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DocumentForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Textiles (Quota) Import Licence - Add supporting document",
        }

        return render(
            request, "web/domains/case/import/textiles/add_supporting_document.html", context
        )


@require_GET
@login_required
def view_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: TextilesApplication = get_object_or_404(TextilesApplication, pk=application_pk)

    return view_application_file(
        request.user, application, application.supporting_documents, document_pk, "import"
    )


@require_POST
@login_required
def delete_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: TextilesApplication = get_object_or_404(
            TextilesApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:textiles:edit", kwargs={"application_pk": application_pk}))
