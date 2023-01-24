from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import OuterRef, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.fa_dfl.forms import (
    DFLSupplementaryInfoForm,
    DFLSupplementaryReportForm,
)
from web.domains.case._import.fa_oil.forms import (
    OILSupplementaryInfoForm,
    OILSupplementaryReportForm,
)
from web.domains.case._import.fa_sil.forms import (
    SILSupplementaryInfoForm,
    SILSupplementaryReportForm,
)
from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.domains.case.utils import check_application_permission, view_application_file
from web.domains.file.utils import create_file_model
from web.flow.models import ProcessTypes, Task
from web.models import (
    DFLApplication,
    ImportApplication,
    ImportContact,
    OpenIndividualLicenceApplication,
    SILApplication,
)
from web.types import AuthenticatedHttpRequest

from .forms import (
    ImportContactKnowBoughtFromForm,
    ImportContactLegalEntityForm,
    ImportContactPersonForm,
    UserImportCertificateForm,
)
from .types import (
    FaImportApplication,
    FaSupplementaryInfo,
    FaSupplementaryInfoFormT,
    FaSupplementaryReport,
    FaSupplementaryReportFormT,
)


# Note: this has been replaced by the following:
# web/domains/case/views/views_email.py -> def manage_case_emails
# however some of the functionality in web/domains/case/import/fa/manage-constabulary-emails.html
# doesn't appear to have been ported over.
@login_required
@permission_required("web.ilb_admin", raise_exception=True)
def manage_constabulary_emails(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        case_progress.application_in_processing(application)

        context = {
            "process": application,
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
def manage_import_contacts(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        if request.method == "POST":
            form = ImportContactKnowBoughtFromForm(data=request.POST, application=application)

            if form.is_valid():
                application.know_bought_from = form.cleaned_data["know_bought_from"]
                application.save()

                return redirect(
                    reverse(
                        "import:fa:manage-import-contacts",
                        kwargs={"application_pk": application_pk},
                    )
                )
        else:
            form = ImportContactKnowBoughtFromForm(
                initial={"know_bought_from": application.know_bought_from},
                application=application,
            )

        context = {
            "process": application,
            "contacts": application.importcontact_set.all(),
            "page_title": "Firearms & Ammunition - Contacts",
            "case_type": "import",
            "form": form,
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
            template = "web/domains/case/import/fa/provide-report/import-contacts.html"
        else:
            application.check_expected_status([ImpExpStatus.IN_PROGRESS, ImpExpStatus.PROCESSING])
            application.get_expected_task(Task.TaskType.PREPARE, select_for_update=False)
            template = "web/domains/case/import/fa/import-contacts/create.html"

        if request.method == "POST":
            form = form_class(data=request.POST)

            if form.is_valid():
                import_contact = form.save(commit=False)
                import_contact.import_application = application
                import_contact.entity = entity
                import_contact.save()

                # Assume known_bought_from is True if we are adding an import contact
                _update_know_bought_from(application)

                if application.status == application.Statuses.COMPLETED:
                    url = reverse(
                        "import:fa:provide-report", kwargs={"application_pk": application_pk}
                    )
                else:
                    url = reverse(
                        "import:fa:manage-import-contacts",
                        kwargs={"application_pk": application_pk},
                    )

                return redirect(url)
        else:
            form = form_class()

        context = {
            "process": application,
            "form": form,
            "page_title": "Firearms & Ammunition - Create Contact",
            "case_type": "import",
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
            template = "web/domains/case/import/fa/provide-report/import-contacts.html"
        else:
            application.check_expected_status([ImpExpStatus.IN_PROGRESS, ImpExpStatus.PROCESSING])
            application.get_expected_task(Task.TaskType.PREPARE, select_for_update=False)
            template = "web/domains/case/import/fa/import-contacts/edit.html"

        if request.method == "POST":
            form = form_class(data=request.POST, instance=person)

            if form.is_valid():
                form.save()

                if application.status == application.Statuses.COMPLETED:
                    url = reverse(
                        "import:fa:provide-report", kwargs={"application_pk": application_pk}
                    )

                else:
                    url = reverse(
                        "import:fa:manage-import-contacts",
                        kwargs={"application_pk": application_pk},
                    )

                return redirect(url)

        else:
            form = form_class(instance=person)

        context = {
            "process": application,
            "form": form,
            "page_title": "Firearms & Ammunition - Edit Contact",
            "case_type": "import",
        }

        return render(request, template, context)


@require_POST
@login_required
def delete_import_contact(
    request: AuthenticatedHttpRequest, *, application_pk: int, entity: str, contact_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        application: FaImportApplication = _get_fa_application(import_application)
        check_application_permission(application, request.user, "import")
        application.check_expected_status([ImpExpStatus.IN_PROGRESS, ImpExpStatus.COMPLETED])

        contact = application.importcontact_set.get(pk=contact_pk)

        if application.status == ImpExpStatus.COMPLETED:
            if application.supplementary_info.reports.filter(bought_from=contact).exists():
                messages.error(
                    request,
                    f"Cannot delete {contact} who is set as bought from in a supplementary report.",
                )
            else:
                contact.delete()

            return redirect(
                reverse("import:fa:provide-report", kwargs={"application_pk": application.pk})
            )

        else:
            contact.delete()

            return redirect(
                reverse(
                    "import:fa:manage-import-contacts", kwargs={"application_pk": application_pk}
                )
            )


@login_required
def manage_certificates(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    """View to manage common certificates across all firearms applications.

    Extended to include application specific certificates for FA-SIL applications.
    """

    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)
        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        selected_verified = application.verified_certificates.filter(pk=OuterRef("pk")).values("pk")
        verified_certificates = application.importer.firearms_authorities.filter(
            is_active=True
        ).annotate(selected=selected_verified)

        extra_context = {}

        # FA-SIL specific context
        if application.process_type == ProcessTypes.FA_SIL:
            verified_section5 = application.importer.section5_authorities.currently_active()
            available_verified_section5 = verified_section5.exclude(
                pk__in=application.verified_section5.all()
            )
            extra_context["user_section5"] = application.user_section5.filter(is_active=True)
            extra_context["verified_section5"] = verified_section5
            extra_context["available_verified_section5"] = available_verified_section5
            extra_context["selected_section5"] = application.verified_section5.all()

        context = {
            "process": application,
            "certificates": application.user_imported_certificates.active(),
            "verified_certificates": verified_certificates,
            "page_title": "Firearms and Ammunition - Certificates",
            "case_type": "import",
        } | extra_context

        return render(request, "web/domains/case/import/fa/certificates/manage.html", context)


@login_required
def create_certificate(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)
        check_application_permission(application, request.user, "import")

        case_progress.application_in_progress(application)

        if request.method == "POST":
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
            "process": application,
            "form": form,
            "page_title": "Firearms and Ammunition - Create Certificate",
            "case_type": "import",
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

        case_progress.application_in_progress(application)

        if request.method == "POST":
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
            "process": application,
            "form": form,
            "page_title": f"Firearms and Ammunition - Edit Certificate '{certificate.reference}'",
            "certificate": certificate,
            "case_type": "import",
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
        case_progress.application_in_progress(application)

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

        case_progress.application_in_progress(application)

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

        case_progress.application_in_progress(application)

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

        case_progress.application_in_progress(application)

        context = {
            "process": application,
            "case_type": "import",
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
        application.check_expected_status([ImpExpStatus.COMPLETED])

        form_class = _get_supplementary_info_form(application)

        if request.method == "POST":
            form = form_class(
                data=request.POST, instance=application.supplementary_info, application=application
            )

            if form.is_valid():
                supplementary_info = form.save(commit=False)
                supplementary_info.is_complete = True
                supplementary_info.completed_datetime = timezone.now()
                supplementary_info.completed_by = request.user
                supplementary_info.save()

                return redirect(
                    reverse("import:fa:provide-report", kwargs={"application_pk": application.pk})
                )

            elif form.non_field_errors():
                messages.error(request, form.non_field_errors()[0])

        else:
            form = form_class(instance=application.supplementary_info, application=application)

        context = {
            "process": application,
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Firearms Supplementary Information Overview",
            "report_type": _get_report_type(application),
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/fa/provide-report/report-info.html",
            context=context,
        )


@login_required
@require_POST
def reopen_report(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")

        application.supplementary_info.is_complete = False
        application.supplementary_info.completed_datetime = None
        application.supplementary_info.completed_by = None
        application.supplementary_info.save()

        return redirect(
            reverse("import:fa:provide-report", kwargs={"application_pk": application.pk})
        )


@login_required
def create_report(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )

        application: FaImportApplication = _get_fa_application(import_application)

        check_application_permission(application, request.user, "import")
        application.check_expected_status([ImpExpStatus.COMPLETED])

        supplementary_info: FaSupplementaryInfo = application.supplementary_info
        form_class = _get_supplementary_report_form(application)

        if request.method == "POST":
            form = form_class(data=request.POST, application=application)

            if form.is_valid():
                report: FaSupplementaryReport = form.save(commit=False)
                report.supplementary_info = supplementary_info
                report.save()

                return redirect(
                    reverse(
                        "import:fa:edit-report",
                        kwargs={"application_pk": application.pk, "report_pk": report.pk},
                    )
                )
        else:
            form = form_class(application=application)

        context = {
            "process": application,
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Add Firearm Supplementary Report",
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
        application.check_expected_status([ImpExpStatus.COMPLETED])

        supplementary_info: FaSupplementaryInfo = application.supplementary_info
        report: FaSupplementaryReport = supplementary_info.reports.get(pk=report_pk)
        report_type = _get_report_type(application)
        form_class = _get_supplementary_report_form(application)

        if request.method == "POST":
            form = form_class(data=request.POST, instance=report, application=application)

            if form.is_valid():
                report.save()

                if not _validate_firearms_details(report, application):
                    messages.error(
                        request,
                        "You must provide firearms details for at least one goods line before submitting a report",
                    )
                else:
                    return redirect(
                        reverse(
                            "import:fa:provide-report", kwargs={"application_pk": application.pk}
                        )
                    )

        else:
            form = form_class(instance=report, application=application)

        context = {
            "process": application,
            "case_type": "import",
            "contacts": application.importcontact_set.all(),
            "page_title": "Edit Firearm Supplementary Report",
            "form": form,
            "report": report,
            "report_type": report_type,
        }

        return render(
            request=request,
            template_name=f"web/domains/case/import/fa/provide-report/edit-report-{report_type}.html",
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
) -> type[ImportContactLegalEntityForm | ImportContactPersonForm]:

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


def _get_supplementary_info_form(application: FaImportApplication) -> FaSupplementaryInfoFormT:
    if application.process_type == ProcessTypes.FA_OIL:
        form = OILSupplementaryInfoForm
    elif application.process_type == ProcessTypes.FA_DFL:
        form = DFLSupplementaryInfoForm
    elif application.process_type == ProcessTypes.FA_SIL:
        form = SILSupplementaryInfoForm
    else:
        raise NotImplementedError(f"Unknown Firearm process_type: {application.process_type}")
    return form


def _get_supplementary_report_form(application: FaImportApplication) -> FaSupplementaryReportFormT:
    if application.process_type == ProcessTypes.FA_OIL:
        form = OILSupplementaryReportForm
    elif application.process_type == ProcessTypes.FA_DFL:
        form = DFLSupplementaryReportForm
    elif application.process_type == ProcessTypes.FA_SIL:
        form = SILSupplementaryReportForm
    else:
        raise NotImplementedError(f"Unknown Firearm process_type: {application.process_type}")
    return form


def _get_report_type(application: FaImportApplication) -> str:
    if application.process_type == ProcessTypes.FA_OIL:
        report_type = "oil"
    elif application.process_type == ProcessTypes.FA_DFL:
        report_type = "dfl"
    elif application.process_type == ProcessTypes.FA_SIL:
        report_type = "sil"
    else:
        raise NotImplementedError(f"Unknown Firearm process_type: {application.process_type}")
    return report_type


def _validate_firearms_details(
    report: FaSupplementaryReport, application: FaImportApplication
) -> bool:
    if application.process_type in [ProcessTypes.FA_DFL, ProcessTypes.FA_OIL]:
        if report.firearms.filter(Q(is_upload=True) | Q(is_manual=True)).exists():
            return True

    if application.process_type == ProcessTypes.FA_SIL:

        sections = [
            report.section1_firearms,
            report.section2_firearms,
            report.section5_firearms,
            report.section582_obsolete_firearms,
            report.section582_other_firearms,
            report.section_legacy_firearms,
        ]

        if any(
            section.filter(Q(is_upload=True) | Q(is_manual=True)).exists() for section in sections
        ):
            return True

    return False
