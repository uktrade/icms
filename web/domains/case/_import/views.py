from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from web.domains.case._import.forms import (
    CreateOILForm,
    PrepareOILForm,
    UserImportCertificateForm,
)
from web.domains.case._import.models import (
    ImportApplication,
    OpenIndividualLicenceApplication,
    UserImportCertificate,
)
from web.domains.file.views import handle_uploaded_file
from web.flow.models import Task


class ImportApplicationChoiceView(TemplateView, PermissionRequiredMixin):
    template_name = "web/domains/case/import/choice.html"
    permission_required = "web.importer_access"


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_oil(request):
    with transaction.atomic():
        if request.POST:
            form = CreateOILForm(request.user, request.POST)
            if form.is_valid():
                application = form.save(commit=False)
                application.process_type = OpenIndividualLicenceApplication.PROCESS_TYPE
                application.created_by = request.user
                application.last_updated_by = request.user
                application.submitted_by = request.user
                application.save()

                Task.objects.create(process=application, task_type="prepare", owner=request.user)
                return redirect(reverse("edit-oil", kwargs={"pk": application.pk}))
        else:
            form = CreateOILForm(request.user)

        context = {"form": form, "page_title": "Open Individual Import Licence"}
        return render(request, "web/domains/case/import/firearms/oil/create.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_oil(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = PrepareOILForm(data=request.POST, instance=application)

            if form.is_valid():
                form.save()

                return redirect(reverse("edit-oil", kwargs={"pk": pk}))

        else:
            form = PrepareOILForm(instance=application, initial={"contact": request.user})

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Open Individual Import Licence",
        }

        return render(request, "web/domains/case/import/firearms/oil/edit.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def list_user_import_certificates(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "certificates": application.userimportcertificate_set.all(),
            "page_title": "Open Individual Import Licence - Certificates",
        }

        return render(request, "web/domains/case/import/firearms/certificates/list.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_user_import_certificate(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = UserImportCertificateForm(data=request.POST, files=request.FILES)
            document = request.FILES.get("document")

            if form.is_valid():
                certificate = form.save(commit=False)
                certificate.import_application = application
                certificate.save()
                handle_uploaded_file(document, request.user, certificate.files)

                return redirect(
                    reverse(
                        "edit-user-import-certificate",
                        kwargs={"application_pk": pk, "certificate_pk": certificate.pk},
                    )
                )
        else:
            form = UserImportCertificateForm()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Open Individual Import Licence - Create Certificate",
        }

        return render(request, "web/domains/case/import/firearms/certificates/create.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_user_import_certificate(request, application_pk, certificate_pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )
        certificate = get_object_or_404(UserImportCertificate, pk=certificate_pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if request.POST:
            form = UserImportCertificateForm(data=request.POST, instance=certificate)

            if form.is_valid():
                certificate = form.save()
                document = request.FILES.get("document")
                if document:
                    handle_uploaded_file(document, request.user, certificate.files)

                return redirect(
                    reverse(
                        "edit-user-import-certificate",
                        kwargs={"application_pk": application_pk, "certificate_pk": certificate_pk},
                    )
                )

        else:
            form = UserImportCertificateForm(instance=certificate)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": f"Open Individual Import Licence - Edit Certificate '{certificate.reference}'",
            "certificate": certificate,
        }

        return render(request, "web/domains/case/import/firearms/certificates/edit.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
@require_POST
def archive_user_import_certificate_file(request, application_pk, certificate_pk, file_pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )
        application.get_task(OpenIndividualLicenceApplication.IN_PROGRESS, "prepare")
        certificate = get_object_or_404(UserImportCertificate, pk=certificate_pk)

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        document = certificate.files.get(pk=file_pk)
        document.is_active = False
        document.save()

        return redirect(
            reverse(
                "edit-user-import-certificate",
                kwargs={"application_pk": application_pk, "certificate_pk": certificate_pk},
            )
        )
