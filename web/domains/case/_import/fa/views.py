from typing import Type, Union

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import OuterRef
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from web.domains.case._import.fa.forms import (
    ConstabularyEmailForm,
    ConstabularyEmailResponseForm,
    ImportContactLegalEntityForm,
    ImportContactPersonForm,
    UserImportCertificateForm,
)
from web.domains.case.views import check_application_permission, view_application_file
from web.domains.file.utils import create_file_model
from web.domains.template.models import Template
from web.models import (
    ConstabularyEmail,
    DFLApplication,
    ImportApplication,
    ImportContact,
    OpenIndividualLicenceApplication,
    SILApplication,
)
from web.notify import email
from web.types import AuthenticatedHttpRequest
from web.utils.s3 import get_file_from_s3, get_s3_client

FaImportApplication = Union[OpenIndividualLicenceApplication, DFLApplication, SILApplication]
FaImportApplicationT = Type[FaImportApplication]


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

        task = application.get_task(ImportApplication.Statuses.SUBMITTED, "process")

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
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def create_constabulary_email(
    request: AuthenticatedHttpRequest, *, application_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        application.get_task(ImportApplication.Statuses.SUBMITTED, "process")

        template = Template.objects.get(is_active=True, template_code="IMA_CONSTAB_EMAIL")
        # TODO: replace with case reference
        goods_description = """Firearms, component parts thereof, or ammunition of any applicable
commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended."""
        body = template.get_content(
            {
                "CASE_REFERENCE": application.pk,
                "IMPORTER_NAME": application.importer.display_name,
                "IMPORTER_ADDRESS": application.importer_office,
                "GOODS_DESCRIPTION": goods_description,
                "CASE_OFFICER_NAME": request.user.full_name,
                "CASE_OFFICER_EMAIL": settings.ILB_CONTACT_EMAIL,
                "CASE_OFFICER_PHONE": settings.ILB_CONTACT_PHONE,
            }
        )

        constabulary_email = ConstabularyEmail.objects.create(
            import_application=import_application,
            status=ConstabularyEmail.DRAFT,
            email_subject=template.template_title,
            email_body=body,
            email_cc_address_list=settings.ICMS_FIREARMS_HOMEOFFICE_EMAIL,
        )

        return redirect(
            reverse(
                "import:fa:edit-constabulary-email",
                kwargs={
                    "application_pk": application.pk,
                    "constabulary_email_pk": constabulary_email.pk,
                },
            )
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def edit_constabulary_email(
    request: AuthenticatedHttpRequest, *, application_pk: int, constabulary_email_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        task = application.get_task(ImportApplication.Statuses.SUBMITTED, "process")
        constabulary_email: ConstabularyEmail = get_object_or_404(
            application.constabulary_emails.filter(is_active=True), pk=constabulary_email_pk
        )

        if request.POST:
            form = ConstabularyEmailForm(request.POST, instance=constabulary_email)
            if form.is_valid():
                constabulary_email = form.save()

                if "send" in request.POST:
                    attachments = []
                    s3_client = get_s3_client()

                    for document in constabulary_email.attachments.all():
                        file_content = get_file_from_s3(document.path, client=s3_client)
                        attachments.append((document.filename, file_content))

                    email.send_email(
                        constabulary_email.email_subject,
                        constabulary_email.email_body,
                        [constabulary_email.email_to],
                        constabulary_email.email_cc_address_list.split(","),
                        attachments,
                    )

                    constabulary_email.status = ConstabularyEmail.OPEN
                    constabulary_email.email_sent_datetime = timezone.now()
                    constabulary_email.save()

                    return redirect(
                        reverse(
                            "import:fa:manage-constabulary-emails",
                            kwargs={
                                "application_pk": application_pk,
                            },
                        )
                    )

                return redirect(
                    reverse(
                        "import:fa:edit-constabulary-email",
                        kwargs={
                            "application_pk": application_pk,
                            "constabulary_email_pk": constabulary_email_pk,
                        },
                    )
                )
        else:
            form = ConstabularyEmailForm(instance=constabulary_email)

        context = {
            "process": application,
            "task": task,
            "page_title": "Edit Constabulary Email",
            "case_type": "import",
            "form": form,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/fa/edit-constabulary-email.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def archive_constabulary_email(
    request: AuthenticatedHttpRequest, *, application_pk: int, constabulary_email_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        application.get_task(ImportApplication.Statuses.SUBMITTED, "process")
        constabulary_email = get_object_or_404(ConstabularyEmail, pk=constabulary_email_pk)

        constabulary_email.is_active = False
        constabulary_email.save()

        return redirect(
            reverse(
                "import:fa:manage-constabulary-emails",
                kwargs={
                    "application_pk": application_pk,
                },
            )
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def add_response_constabulary_email(
    request: AuthenticatedHttpRequest, *, application_pk: int, constabulary_email_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        task = application.get_task(ImportApplication.Statuses.SUBMITTED, "process")
        constabulary_email = get_object_or_404(ConstabularyEmail, pk=constabulary_email_pk)

        if request.POST:
            form = ConstabularyEmailResponseForm(request.POST, instance=constabulary_email)
            if form.is_valid():
                constabulary_email = form.save(commit=False)
                constabulary_email.status = ConstabularyEmail.CLOSED
                constabulary_email.email_closed_datetime = timezone.now()
                constabulary_email.save()

                return redirect(
                    reverse(
                        "import:fa:manage-constabulary-emails",
                        kwargs={
                            "application_pk": application_pk,
                        },
                    )
                )
        else:
            form = ConstabularyEmailResponseForm(instance=constabulary_email)

        context = {
            "process": application,
            "task": task,
            "page_title": "Add Response for Constabulary Email",
            "case_type": "import",
            "form": form,
            "object": constabulary_email,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/fa/add-response-constabulary-email.html",
            context=context,
        )


@login_required
def list_import_contacts(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

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

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = form_class(data=request.POST)

            if form.is_valid():
                import_contact = form.save(commit=False)
                import_contact.import_application = application
                import_contact.entity = entity
                import_contact.save()

                # Assume known_bought_from is True if we are adding an import contact
                _update_know_bought_from(application)

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

        return render(request, "web/domains/case/import/fa/import-contacts/create.html", context)


@login_required
@permission_required("web.importer_access", raise_exception=True)
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

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

        if request.POST:
            form = form_class(data=request.POST, instance=person)

            if form.is_valid():
                form.save()

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

        return render(request, "web/domains/case/import/fa/import-contacts/edit.html", context)


@login_required
def manage_certificates(request: AuthenticatedHttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)
        check_application_permission(application, request.user, "import")

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

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

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

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

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

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
        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

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

        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

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

        application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

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

        task = application.get_task(ImportApplication.Statuses.IN_PROGRESS, "prepare")

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
