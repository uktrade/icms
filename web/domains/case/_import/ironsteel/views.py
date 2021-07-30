from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from storages.backends.s3boto3 import S3Boto3StorageFile

from web.domains.case._import.models import ImportApplication
from web.domains.case.forms import DocumentForm
from web.domains.case.views import check_application_permission, view_application_file
from web.domains.file.utils import create_file_model
from web.types import AuthenticatedHttpRequest
from web.utils.commodity import get_category_commodity_group_data

from .. import views as import_views
from .forms import AddCertificateForm, EditCertificateForm, EditIronSteelForm
from .models import IronSteelApplication


@login_required
def edit_ironsteel(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: IronSteelApplication = get_object_or_404(
            IronSteelApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = EditIronSteelForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:ironsteel:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditIronSteelForm(instance=application, initial={"contact": request.user})

        supporting_documents = application.supporting_documents.filter(is_active=True)
        certificates = application.certificates.filter(is_active=True)

        category_commodity_groups = get_category_commodity_group_data(commodity_type="IRON_STEEL")

        if application.category_commodity_group:
            selected_group = category_commodity_groups.get(
                application.category_commodity_group.pk, {}
            )
        else:
            selected_group = {}

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Iron and Steel (Quota) Import Licence - Edit",
            "supporting_documents": supporting_documents,
            "category_commodity_groups": category_commodity_groups,
            "commodity_group_label": selected_group.get("label", ""),
            "certificates": certificates,
        }

        return render(request, "web/domains/case/import/ironsteel/edit.html", context)


@login_required
def submit_ironsteel(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    # TODO: implement (ICMSLST-885)
    raise NotImplementedError


@login_required
def add_document(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: IronSteelApplication = get_object_or_404(
            IronSteelApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = DocumentForm(data=request.POST, files=request.FILES)

            if form.is_valid():
                document = form.cleaned_data.get("document")
                create_file_model(document, request.user, application.supporting_documents)

                return redirect(
                    reverse("import:ironsteel:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = DocumentForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Iron and Steel (Quota) Import Licence - Add supporting document",
        }

        return render(
            request, "web/domains/case/import/ironsteel/add_supporting_document.html", context
        )


@require_GET
@login_required
def view_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application: IronSteelApplication = get_object_or_404(IronSteelApplication, pk=application_pk)

    return view_application_file(
        request.user, application, application.supporting_documents, document_pk, "import"
    )


@require_POST
@login_required
def delete_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: IronSteelApplication = get_object_or_404(
            IronSteelApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        document = application.supporting_documents.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:ironsteel:edit", kwargs={"application_pk": application_pk}))


@login_required
def add_certificate(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: IronSteelApplication = get_object_or_404(
            IronSteelApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = AddCertificateForm(data=request.POST, files=request.FILES)

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
                    application.certificates,
                    extra_args=extra_args,
                )

                return redirect(
                    reverse("import:ironsteel:edit", kwargs={"application_pk": application_pk})
                )
        else:
            form = AddCertificateForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Iron and Steel (Quota) Import Licence - Add certificate",
        }

        return render(request, "web/domains/case/import/ironsteel/add_certificate.html", context)


@require_GET
@login_required
def view_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    application = get_object_or_404(IronSteelApplication, pk=application_pk)

    return import_views.view_file(request, application, application.certificates, document_pk)


@require_POST
@login_required
def delete_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            IronSteelApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        document = application.certificates.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:ironsteel:edit", kwargs={"application_pk": application_pk}))


@login_required
def edit_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            IronSteelApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        document = application.certificates.get(pk=document_pk)

        if request.POST:
            form = EditCertificateForm(data=request.POST, instance=document)

            if form.is_valid():
                form.save()

                return redirect(
                    reverse("import:ironsteel:edit", kwargs={"application_pk": application_pk})
                )

        else:
            form = EditCertificateForm(instance=document)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Iron and Steel (Quota) Import Licence - Edit certificate",
        }

        return render(request, "web/domains/case/import/ironsteel/edit_certificate.html", context)
