from typing import Type, Union

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from web.domains.case._import.fa.forms import (
    ConstabularyEmailForm,
    ConstabularyEmailResponseForm,
)
from web.domains.template.models import Template
from web.models import (  # DFLApplication,; SILApplication
    ConstabularyEmail,
    ImportApplication,
    OpenIndividualLicenceApplication,
)
from web.notify import email
from web.utils.s3 import get_file_from_s3, get_s3_client

FaImportApplication = Union[
    OpenIndividualLicenceApplication,
    # DFLApplication,
    # SILApplication
]
FaImportApplicationT = Type[FaImportApplication]


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
def manage_constabulary_emails(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        # TODO: Why is this select for update
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        task = application.get_task(ImportApplication.SUBMITTED, "process")

        context = {
            "process": application,
            "task": task,
            "page_title": "Constabulary Emails",
            "constabulary_emails": import_application.constabulary_emails.filter(is_active=True),
            # TODO: This key is only for FA-OIL applications
            "verified_certificates": application.verified_certificates.all(),
        }

        return render(
            request=request,
            template_name="web/domains/case/import/fa/manage-constabulary-emails.html",
            context=context,
        )


@login_required
@permission_required("web.reference_data_access", raise_exception=True)
@require_POST
def create_constabulary_email(request: HttpRequest, *, application_pk: int) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        application.get_task(ImportApplication.SUBMITTED, "process")

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
    request: HttpRequest, *, application_pk: int, constabulary_email_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        task = application.get_task(ImportApplication.SUBMITTED, "process")
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
def delete_constabulary_email(
    request: HttpRequest, *, application_pk: int, constabulary_email_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        application.get_task(ImportApplication.SUBMITTED, "process")
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
    request: HttpRequest, *, application_pk: int, constabulary_email_pk: int
) -> HttpResponse:
    with transaction.atomic():
        import_application: ImportApplication = get_object_or_404(
            ImportApplication.objects.select_for_update(), pk=application_pk
        )
        application: FaImportApplication = _get_fa_application(import_application)

        task = application.get_task(ImportApplication.SUBMITTED, "process")
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
            "form": form,
            "object": constabulary_email,
        }

        return render(
            request=request,
            template_name="web/domains/case/import/fa/add-response-constabulary-email.html",
            context=context,
        )


def _get_fa_application(application: ImportApplication) -> FaImportApplication:
    process_type_link = {
        OpenIndividualLicenceApplication.PROCESS_TYPE: "openindividuallicenceapplication",
        # DFLApplication.PROCESS_TYPE: "dflapplication",
        # SILApplication.PROCESS_TYPE: "silapplication",
    }

    try:
        link = process_type_link[application.process_type]
    except KeyError:
        raise NotImplementedError(f"Unknown Firearm process_type: {application.process_type}")

    # e.g. application.openindividuallicenceapplication to get access to OpenIndividualLicenceApplication
    firearms_application: FaImportApplication = getattr(application, link)

    return firearms_application
