from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from web.domains.case._import.firearms.forms import (
    ChecklistFirearmsOILApplicationForm,
    ImportContactLegalEntityForm,
    ImportContactPersonForm,
    PrepareOILForm,
    SubmitOILForm,
    UserImportCertificateForm,
)
from web.domains.case._import.models import ImportApplication, ImportContact
from web.domains.file.views import handle_uploaded_file
from web.domains.template.models import Template
from web.flow.models import Task

from .models import OpenIndividualLicenceApplication, UserImportCertificate


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

                return redirect(reverse("import:edit-oil", kwargs={"pk": pk}))

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
            "verified_certificates": application.importer.firearms_authorities.active(),
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
                        "import:edit-user-import-certificate",
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
                        "import:edit-user-import-certificate",
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


@login_required
@permission_required("web.importer_access", raise_exception=True)
def list_import_contacts(request, pk):
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
            "contacts": application.importcontact_set.all(),
            "page_title": "Open Individual Import Licence - Contacts",
        }

        return render(
            request, "web/domains/case/import/firearms/import-contacts/list.html", context
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def create_import_contact(request, pk, entity):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if entity == ImportContact.LEGAL:
            Form = ImportContactLegalEntityForm
        else:
            Form = ImportContactPersonForm

        if request.POST:
            form = Form(data=request.POST, files=request.FILES)

            if form.is_valid():
                import_contact = form.save(commit=False)
                import_contact.import_application = application
                import_contact.entity = entity
                import_contact.save()

                if application.know_bought_from != OpenIndividualLicenceApplication.YES:
                    application.know_bought_from = OpenIndividualLicenceApplication.YES
                    application.save()

                return redirect(
                    reverse(
                        "import:edit-import-contact",
                        kwargs={
                            "application_pk": pk,
                            "entity": entity,
                            "contact_pk": import_contact.pk,
                        },
                    )
                )
        else:
            form = Form()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Open Individual Import Licence",
        }

        return render(
            request, "web/domains/case/import/firearms/import-contacts/create.html", context
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def edit_import_contact(request, application_pk, entity, contact_pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )
        person = get_object_or_404(ImportContact, pk=contact_pk)

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        if entity == ImportContact.LEGAL:
            Form = ImportContactLegalEntityForm
        else:
            Form = ImportContactPersonForm

        if request.POST:
            form = Form(data=request.POST, instance=person)

            if form.is_valid():
                certificate = form.save()
                document = request.FILES.get("document")
                if document:
                    handle_uploaded_file(document, request.user, certificate.files)

                return redirect(
                    reverse(
                        "import:edit-import-contact",
                        kwargs={
                            "application_pk": application_pk,
                            "entity": entity,
                            "contact_pk": contact_pk,
                        },
                    )
                )

        else:
            form = Form(instance=person)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Open Individual Import Licence - Edit Import Contact",
        }

        return render(
            request, "web/domains/case/import/firearms/import-contacts/edit.html", context
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def validate_oil(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        know_bought_from = application.know_bought_from is not None
        if know_bought_from == OpenIndividualLicenceApplication.YES:
            know_bought_from = application.importcontact_set.exists()

        certificates = (
            application.userimportcertificate_set.exists()
            or application.verified_certificates.exists()
        )
        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Open Individual Import Licence - Validation",
            "certificates": certificates,
            "know_bought_from": know_bought_from,
        }

        return render(request, "web/domains/case/import/firearms/oil/validation.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
def submit_oil(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        know_bought_from = application.know_bought_from is not None
        if know_bought_from == OpenIndividualLicenceApplication.YES:
            know_bought_from = application.importcontact_set.exists()
        certificates = (
            application.userimportcertificate_set.exists()
            or application.verified_certificates.exists()
        )
        if not application.commodity_group or not know_bought_from or not certificates:
            return redirect(reverse("import:oil-validation", kwargs={"pk": application.pk}))

        if request.POST:
            form = SubmitOILForm(data=request.POST)

            if form.is_valid():
                application.status = ImportApplication.SUBMITTED
                application.save()

                task.is_active = False
                task.finished = timezone.now()
                task.save()

                Task.objects.create(process=application, task_type="process", previous=task)

                return redirect(reverse("home"))

        else:
            form = SubmitOILForm()

        declaration = Template.objects.filter(
            is_active=True,
            template_type=Template.DECLARATION,
            application_domain=Template.IMPORT_APPLICATION,
            template_name="Declaration of Truth",
        ).first()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Open Individual Import Licence - Submit Application",
            "form": form,
            "declaration": declaration,
        }

        return render(request, "web/domains/case/import/firearms/oil/submit.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
@require_POST
def toggle_verified_firearms(request, application_pk, authority_pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )
        firearms_authority = get_object_or_404(
            application.importer.firearms_authorities.active(), pk=authority_pk
        )

        application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        certificate, created = application.verified_certificates.get_or_create(
            firearms_authority=firearms_authority
        )
        if not created:
            certificate.delete()

        return redirect(
            reverse("import:list-user-import-certificates", kwargs={"pk": application_pk})
        )


@login_required
@permission_required("web.importer_access", raise_exception=True)
def view_verified_firearms(request, application_pk, authority_pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=application_pk
        )
        firearms_authority = get_object_or_404(
            application.importer.firearms_authorities.active(), pk=authority_pk
        )

        task = application.get_task(ImportApplication.IN_PROGRESS, "prepare")

        if not request.user.has_perm("web.is_contact_of_importer", application.importer):
            raise PermissionDenied

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Open Individual Import Licence - Verified Certificate",
            "firearms_authority": firearms_authority,
        }
        return render(
            request, "web/domains/case/import/firearms/certificates/view-verified.html", context
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_checklist(request, pk):
    with transaction.atomic():
        application = get_object_or_404(
            OpenIndividualLicenceApplication.objects.select_for_update(), pk=pk
        )
        task = application.get_task(ImportApplication.SUBMITTED, "process")
        checklist, _ = application.checklists.get_or_create()

        if request.POST:
            form = ChecklistFirearmsOILApplicationForm(request.POST, instance=checklist)
            if form.is_valid():
                form.save()
                return redirect(reverse("import:manage-checklist", kwargs={"pk": pk}))
        else:
            form = ChecklistFirearmsOILApplicationForm(instance=checklist)

        context = {
            "process": application,
            "task": task,
            "page_title": "Open Individual Import Licence - Checklist",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/management/checklist.html",
            context=context,
        )
