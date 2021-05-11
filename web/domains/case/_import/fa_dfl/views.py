from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from storages.backends.s3boto3 import S3Boto3StorageFile

from web.domains.case._import.models import ImportApplication
from web.domains.file.utils import create_file_model

from .. import views as import_views
from .forms import (
    AddDLFGoodsCertificateForm,
    EditDLFGoodsCertificateForm,
    PrepareDFLForm,
)
from .models import DFLApplication


def _get_page_title(page: str) -> str:
    return f"Firearms and Ammunition (Deactivated Firearms Licence) - {page}"


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_dlf(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(DFLApplication.objects.select_for_update(), pk=pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = PrepareDFLForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()
                return redirect(reverse("import:fa-dfl:edit", kwargs={"pk": pk}))

        else:
            form = PrepareDFLForm(instance=application, initial={"contact": request.user})

        goods_list = application.goods_certificates.filter(is_active=True).select_related(
            "issuing_country"
        )

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": _get_page_title("Edit"),
            "goods_list": goods_list,
        }

        return render(request, "web/domains/case/import/fa-dfl/edit.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def add_goods_certificate(request: HttpRequest, pk: int) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(DFLApplication.objects.select_for_update(), pk=pk)
        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = AddDLFGoodsCertificateForm(data=request.POST, files=request.FILES)

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
                    application.goods_certificates,
                    extra_args=extra_args,
                )

                return redirect(reverse("import:fa-dfl:edit", kwargs={"pk": pk}))
        else:
            form = AddDLFGoodsCertificateForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": _get_page_title("Add Goods Certificate"),
        }

        return render(request, "web/domains/case/import/fa-dfl/add_goods_certificate.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_goods_certificate(
    request: HttpRequest, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        document = application.goods_certificates.get(pk=document_pk)

        if request.POST:
            form = EditDLFGoodsCertificateForm(data=request.POST, instance=document)

            if form.is_valid():
                form.save()

                return redirect(reverse("import:fa-dfl:edit", kwargs={"pk": application_pk}))

        else:
            form = EditDLFGoodsCertificateForm(instance=document)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": _get_page_title("Edit Goods Certificate"),
        }

        return render(
            request, "web/domains/case/import/fa-dfl/edit_goods_certificate.html", context
        )


@require_GET
@login_required
def view_goods_certificate(
    request: HttpRequest, application_pk: int, document_pk: int
) -> HttpResponse:
    application = get_object_or_404(DFLApplication, pk=application_pk)

    return import_views.view_file(request, application, application.goods_certificates, document_pk)


@require_POST
@login_required
@permission_required("web.importer_access", raise_exception=True)
def delete_goods_certificate(
    request: HttpRequest, application_pk: int, document_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application = get_object_or_404(
            DFLApplication.objects.select_for_update(), pk=application_pk
        )

        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        document = application.goods_certificates.get(pk=document_pk)
        document.is_active = False
        document.save()

        return redirect(reverse("import:fa-dfl:edit", kwargs={"pk": application_pk}))
