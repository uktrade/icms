from typing import Type, Union

from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import OuterRef
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from web.domains.case.utils import (
    check_application_permission,
    get_application_current_task,
    view_application_file,
)
from web.domains.file.utils import create_file_model
from web.flow.models import Task
from web.models import (
    DFLApplication,
    ImportApplication,
    ImportContact,
    OpenIndividualLicenceApplication,
    SILApplication,
)
from web.types import AuthenticatedHttpRequest

from .forms import (
    ImportContactLegalEntityForm,
    ImportContactPersonForm,
    SupplementaryReportForm,
    UserImportCertificateForm,
)
from .models import SupplementaryInfo, SupplementaryReport
from .types import FaImportApplication


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_constabulary_emails(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        task = get_application_current_task(application, "import", Task.TaskType.PROCESS)

        context = {
            "process": application,
            "task": task,
            "page_title": "Constabulary Emails",
            "case_type": "import",
            "constabulary_emails": import_application.constabulary_emails.filter(is_active=True),
            "show_verified_certificates": False,
            "verified_certificates": None,
        }

        if import_application.process_type == OpenIndividualLicenceApplication.PROCESS_TYPE:
            context.update(
                {
                    "show_verified_certificates": True,
                    "verified_certificates": application.verified_certificates.filter(
                        is_active=True
                    ),
                }
            )

        return render(
            request=request,
            template_name="web/domains/case/import/fa/manage-constabulary-emails.html",
            context=context,
        )


@login_required
def list_import_contacts(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "contacts": application.importcontact_set.all(),
            "page_title": "Firearms & Ammunition - Contacts",
        }

        return render(request, "web/domains/case/import/fa/import-contacts/list.html", context)


@login_required
def create_import_contact(
    request: AuthenticatedHttpRequest, *, application_pk: int, entity: str
) -> HttpResponse:
    form_class = _get_entity_form(entity)

    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        if application.status == application.Statuses.COMPLETED:
            task = get_application_current_task(application, "import", Task.TaskType.ACK)
            template = "web/domains/case/import/fa/provide-report/import-contacts.html"
        else:
            task = get_application_current_task(application, "import", Task.TaskType.PREPARE)
            template = "web/domains/case/import/fa/import-contacts/create.html"

        if request.POST:
            form = form_class(data=request.POST)

            if form.is_valid():
                import_contact = form.save(commit=False)
                import_contact.import_application = application
                import_contact.entity = entity
                import_contact.save()

                # Assume known_bought_from is True if we are adding an import contact
                _update_know_bought_from(application)

                if application.status == application.Statuses.COMPLETED:
                    return redirect(
                        reverse(
                            "import:fa:provide-report", kwargs={"application_pk": application.pk}
                        )
                    )

                return redirect(
                    reverse(
                        "import:fa:edit-import-contact",
                        kwargs={
                            "application_pk": application_pk,
                            "entity": entity,
                            "contact_pk": import_contact.pk,
                        },
                    )
                )
        else:
            form = form_class()

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Firearms & Ammunition - Create Contact",
        }

        return render(request, template, context)


@login_required
def edit_import_contact(
    request: AuthenticatedHttpRequest, *, application_pk: int, entity: str, contact_pk: int
) -> HttpResponse:

    form_class = _get_entity_form(entity)

    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")

        person = get_object_or_404(ImportContact, pk=contact_pk)

        if application.status == application.Statuses.COMPLETED:
            task = get_application_current_task(application, "import", Task.TaskType.ACK)
            template = "web/domains/case/import/fa/provide-report/import-contacts.html"
        else:
            task = get_application_current_task(application, "import", Task.TaskType.PREPARE)
            template = "web/domains/case/import/fa/import-contacts/edit.html"

        if request.POST:
            form = form_class(data=request.POST, instance=person)

            if form.is_valid():
                form.save()

                if application.status == application.Statuses.COMPLETED:
                    return redirect(
                        reverse(
                            "import:fa:provide-report", kwargs={"application_pk": application.pk}
                        )
                    )

                return redirect(
                    reverse(
                        "import:fa:edit-import-contact",
                        kwargs={
                            "application_pk": application_pk,
                            "entity": entity,
                            "contact_pk": contact_pk,
                        },
                    )
                )

        else:
            form = form_class(instance=person)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Firearms & Ammunition - Edit Contact",
        }

        return render(request, template, context)


@require_POST
@login_required
def delete_import_contact(
    request: AuthenticatedHttpRequest, *, application_pk: int, entity: str, contact_pk: int
) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        check_application_permission(application, request.user, "import")
        get_application_current_task(application, "import", Task.TaskType.ACK)
        application.importcontact_set.filter(pk=contact_pk).delete()

        return redirect(
            reverse("import:fa:provide-report", kwargs={"application_pk": application.pk})
        )


@login_required
def manage_certificates(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)
        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        selected_verified = application.verified_certificates.filter(pk=OuterRef("pk")).values("pk")
        verified_certificates = application.importer.firearms_authorities.filter(
            is_active=True
        ).annotate(selected=selected_verified)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "certificates": application.user_imported_certificates.active(),
            "verified_certificates": verified_certificates,
            "page_title": "Firearms and Ammunition - Certificates",
        }

        return render(request, "web/domains/case/import/fa/certificates/manage.html", context)


@login_required
def create_certificate(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)
        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        if request.POST:
            form = UserImportCertificateForm(
                data=request.POST, application=application, files=request.FILES
            )

            if form.is_valid():
                document = form.cleaned_data.get("document")

                extra_args = {
                    field: value
                    for (field, value) in form.cleaned_data.items()
                    if field not in ["document"]
                }

                create_file_model(
                    document,
                    request.user,
                    application.user_imported_certificates,
                    extra_args=extra_args,
                )

                return redirect(
                    reverse(
                        "import:fa:manage-certificates", kwargs={"application_pk": application_pk}
                    )
                )
        else:
            form = UserImportCertificateForm(application=application)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": "Firearms and Ammunition - Create Certificate",
        }

        return render(request, "web/domains/case/import/fa/certificates/create.html", context)


@login_required
def edit_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int, certificate_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)
        check_application_permission(application, request.user, "import")

        certificate = get_object_or_404(application.user_imported_certificates, pk=certificate_pk)

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        if request.POST:
            form = UserImportCertificateForm(
                data=request.POST, application=application, instance=certificate
            )

            if form.is_valid():
                form.save()

                return redirect(
                    reverse(
                        "import:fa:manage-certificates",
                        kwargs={"application_pk": application_pk},
                    )
                )

        else:
            form = UserImportCertificateForm(application=application, instance=certificate)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "form": form,
            "page_title": f"Firearms and Ammunition - Edit Certificate '{certificate.reference}'",
            "certificate": certificate,
        }

        return render(request, "web/domains/case/import/fa/certificates/edit.html", context)


@require_GET
@login_required
def view_certificate_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, certificate_pk: int
) -> HttpResponse:
    import_application: ImportApplication = get_object_or_404(ImportApplication, pk=application_pk)
    application: FaImportApplication = _get_fa_application(import_application)

    return view_application_file(
        request.user, application, application.user_imported_certificates, certificate_pk, "import"
    )


@require_POST
@login_required
def archive_certificate(
    request: AuthenticatedHttpRequest, *, application_pk: int, certificate_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")
        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        document = application.user_imported_certificates.get(pk=certificate_pk)
        document.is_active = False
        document.save()

        return redirect(
            reverse("import:fa:manage-certificates", kwargs={"application_pk": application_pk})
        )


@require_POST
@login_required
def add_authority(
    request: AuthenticatedHttpRequest, *, application_pk: int, authority_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        firearms_authority = get_object_or_404(
            application.importer.firearms_authorities.active(), pk=authority_pk
        )

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        application.verified_certificates.add(firearms_authority)

        return redirect(
            reverse("import:fa:manage-certificates", kwargs={"application_pk": application_pk})
        )


@require_POST
@login_required
def delete_authority(
    request: AuthenticatedHttpRequest, *, application_pk: int, authority_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        firearms_authority = get_object_or_404(
            application.importer.firearms_authorities.active(), pk=authority_pk
        )

        get_application_current_task(application, "import", Task.TaskType.PREPARE)

        application.verified_certificates.remove(firearms_authority)

        return redirect(
            reverse("import:fa:manage-certificates", kwargs={"application_pk": application_pk})
        )


@require_GET
@login_required
def view_authority_document(
    request: AuthenticatedHttpRequest, *, application_pk: int, authority_pk: int, document_pk: int
) -> HttpResponse:
    import_application: ImportApplication = get_object_or_404(ImportApplication, pk=application_pk)
    application: FaImportApplication = _get_fa_application(import_application)
    firearms_authority = get_object_or_404(
        application.importer.firearms_authorities.active(), pk=authority_pk
    )

    return view_application_file(
        request.user, application, firearms_authority.files, document_pk, "import"
    )


@login_required
def view_authority(request: AuthenticatedHttpRequest, *, application_pk: int, authority_pk: int):
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        firearms_authority = get_object_or_404(
            application.importer.firearms_authorities.active(), pk=authority_pk
        )

        task = get_application_current_task(application, "import", Task.TaskType.PREPARE)

        context = {
            "process_template": "web/domains/case/import/partials/process.html",
            "process": application,
            "task": task,
            "page_title": "Firearms Authority - Verified Certificate",
            "firearms_authority": firearms_authority,
        }

        return render(
            request, "web/domains/case/import/fa/certificates/view-verified.html", context
        )


@login_required
def provide_report(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.ACK)

        if request.POST:
            # TODO ICMSLST-962 Add additional POST steps here
            application.supplementary_info.is_complete = True
            application.supplementary_info.completed_datetime = timezone.now()
            application.supplementary_info.completed_by = request.user
            application.save()

            return redirect(reverse("workbasket"))

        context = {
            "process": application,
            "task": task,
            "process_template": "web/domains/case/import/partials/process.html",
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Firearms Supplementary Information Overview",
        }

        return render(
            request=request,
            template_name="web/domains/case/import/fa/provide-report/report-info.html",
            context=context,
        )


@login_required
def create_report(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.ACK)

        supplementary_info: SupplementaryInfo = application.supplementary_info

        if request.POST:
            form = SupplementaryReportForm(
                data=request.POST, application=application, supplementary_info=supplementary_info
            )

            if form.is_valid():
                report: SupplementaryReport = form.save()

                return redirect(
                    reverse(
                        "import:fa:edit-report",
                        kwargs={"application_pk": application.pk, "report_pk": report.pk},
                    )
                )
        else:
            form = SupplementaryReportForm(
                application=application, supplementary_info=supplementary_info
            )

        context = {
            "process": application,
            "task": task,
            "process_template": "web/domains/case/import/partials/process.html",
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Firearms Supplementary Information Overview",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/fa/provide-report/create-report.html",
            context=context,
        )


@login_required
def edit_report(
    request: AuthenticatedHttpRequest, *, application_pk: int, report_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        task = get_application_current_task(application, "import", Task.TaskType.ACK)

        supplementary_info: SupplementaryInfo = application.supplementary_info
        report: SupplementaryReport = supplementary_info.reports.get(pk=report_pk)

        if request.POST:
            form = SupplementaryReportForm(
                data=request.POST,
                instance=report,
                application=application,
                supplementary_info=supplementary_info,
            )

            if form.is_valid():
                form.save()

        else:
            form = SupplementaryReportForm(
                instance=report, application=application, supplementary_info=supplementary_info
            )

        context = {
            "process": application,
            "task": task,
            "process_template": "web/domains/case/import/partials/process.html",
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Firearms Supplementary Information Overview",
            "form": form,
            "report": report,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/fa/provide-report/edit-report.html",
            context=context,
        )


@require_POST
@login_required
def delete_report(
    request: AuthenticatedHttpRequest, *, application_pk: int, report_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        application.supplementary_info.reports.filter(pk=report_pk).delete()

        return redirect(
            reverse("import:fa:provide-report", kwargs={"application_pk": application.pk})
        )


def _update_know_bought_from(firearms_application: FaImportApplication) -> None:
    if not firearms_application.know_bought_from:
        firearms_application.know_bought_from = True
        firearms_application.save()


def _get_entity_form(
    entity: str,
) -> Type[Union[ImportContactLegalEntityForm, ImportContactPersonForm]]:

    if entity == ImportContact.LEGAL:
        form_class = ImportContactLegalEntityForm

    elif entity == ImportContact.NATURAL:
        form_class = ImportContactPersonForm

    else:
        raise NotImplementedError(f"View does not support entity type: {entity}")

    return form_class


def _get_fa_application(application: ImportApplication) -> FaImportApplication:
    process_type_link = {
        OpenIndividualLicenceApplication.PROCESS_TYPE: "openindividuallicenceapplication",
        DFLApplication.PROCESS_TYPE: "dflapplication",
        SILApplication.PROCESS_TYPE: "silapplication",
    }

    try:
        link = process_type_link[application.process_type]
    except KeyError:
        raise NotImplementedError(f"Unknown Firearm process_type: {application.process_type}")

    # e.g. application.openindividuallicenceapplication to get access to OpenIndividualLicenceApplication
    firearms_application: FaImportApplication = getattr(application, link)

    return firearms_application
