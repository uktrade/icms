from collections.abc import Collection
from typing import Any

import html2text
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import QuerySet
from django.utils import timezone

from config.celery import app
from web.domains.case.types import ImpOrExp
from web.models import CaseEmail, Exporter, Importer, User, VariationRequest
from web.permissions import get_org_obj_permissions, organisation_get_contacts

from . import utils
from .constants import VariationRequestDescription


@app.task(name="web.notify.email.send_email")
def send_email(
    subject: str,
    body: str,
    recipients: Collection[str],
    cc: Collection[str] = (),
    attachment_ids: tuple[int, ...] = (),
    html_message: str | None = None,
) -> None:
    attachments = utils.get_attachments(attachment_ids)
    message = EmailMultiAlternatives(
        subject, body, settings.EMAIL_FROM, recipients, cc=cc, attachments=attachments
    )

    if html_message:
        message.attach_alternative(html_message, "text/html")

    message.send()


def send_to_contacts(
    subject: str, message: str, contacts: QuerySet[User], html_message: str | None = None
) -> None:
    for contact in contacts:
        send_email.delay(
            subject, message, utils.get_notification_emails(contact), html_message=html_message
        )


def send_to_importer_contacts(
    importer: Importer, subject: str, message: str, html_message: str | None = None
) -> None:
    if importer.type == Importer.INDIVIDUAL:
        # TODO: ICMSLST-1948 Revisit this
        # The importer.user is set when creating an individual importer.
        # However they also get set as a contact so this special case might not be needed.
        if importer.user and importer.user.is_active:
            send_email.delay(
                subject,
                message,
                utils.get_notification_emails(importer.user),
                html_message=html_message,
            )

        return

    obj_perms = get_org_obj_permissions(importer)
    contacts = organisation_get_contacts(importer, perms=[obj_perms.edit.codename])
    send_to_contacts(subject, message, contacts, html_message)


def send_to_all_importers(subject: str, message: str, html_message: str | None = None) -> None:
    importers = Importer.objects.filter(is_active=True)
    for importer in importers:
        send_to_importer_contacts(importer, subject, message, html_message)


def send_to_exporter_contacts(
    exporter: Exporter, subject: str, message: str, html_message: str | None = None
) -> None:
    obj_perms = get_org_obj_permissions(exporter)

    contacts = organisation_get_contacts(exporter, perms=[obj_perms.edit.codename])
    send_to_contacts(subject, message, contacts, html_message)


def send_to_all_exporters(subject: str, message: str, html_message: str | None = None) -> None:
    exporters = Exporter.objects.filter(is_active=True)
    for exporter in exporters:
        send_to_exporter_contacts(exporter, subject, message, html_message)


def send_to_application_contacts(
    application: ImpOrExp, subject: str, message: str, html_message: str | None = None
) -> None:
    contacts = get_application_contacts(application)
    send_to_contacts(subject, message, contacts, html_message)


def get_application_contacts(application: ImpOrExp) -> QuerySet[User]:
    if application.is_import_application():
        org = application.agent or application.importer
    else:
        org = application.agent or application.exporter
    return get_organisation_contacts(org)


def get_organisation_contacts(org):
    obj_perms = get_org_obj_permissions(org)
    return organisation_get_contacts(org, perms=[obj_perms.edit.codename])


@app.task(name="web.notify.email.send_mailshot")
def send_mailshot(
    subject: str,
    message: str,
    html_message: str | None = None,
    to_importers: bool = False,
    to_exporters: bool = False,
) -> None:
    """
    Sends mailshots
    """
    if to_importers:
        send_to_all_importers(subject, message, html_message=html_message)
    if to_exporters:
        send_to_all_exporters(subject, message, html_message=html_message)


def send_case_email(case_email: CaseEmail) -> None:
    attachment_ids = tuple(case_email.attachments.values_list("pk", flat=True))

    send_email.delay(
        case_email.subject,
        case_email.body,
        [case_email.to],
        case_email.cc_address_list,
        attachment_ids,
    )

    case_email.status = CaseEmail.Status.OPEN
    case_email.sent_datetime = timezone.now()
    case_email.save()


def send_html_email(
    template: str,
    context: dict[str, Any],
    contacts: list[User],
) -> None:
    message_html = utils.render_email(template, context)
    message_text = html2text.html2text(message_html)
    send_to_contacts(context["subject"], message_text, contacts, message_html)


def get_variation_request_email_subject(
    description: VariationRequestDescription, application: ImpOrExp
) -> str:
    match description:
        case VariationRequestDescription.CANCELLED:
            return "Variation Request Cancelled"
        case VariationRequestDescription.UPDATE_REQUIRED:
            return "Variation Update Required"
        case VariationRequestDescription.UPDATE_CANCELLED:
            return "Variation Update No Longer Required"
        case VariationRequestDescription.UPDATE_RECEIVED:
            return "Variation Update Received"
        case VariationRequestDescription.REFUSED:
            return f"Variation on application reference {application.reference} has been refused by ILB"
        case _:
            raise ValueError("Unsupported Variation Request Description")


def send_variation_request_email(
    variation_request: VariationRequest,
    description: VariationRequestDescription,
    application: ImpOrExp,
) -> None:
    subject = get_variation_request_email_subject(description, application)

    if description == VariationRequestDescription.CANCELLED:
        contacts = [variation_request.requested_by]
    elif description == VariationRequestDescription.UPDATE_RECEIVED:
        contacts = [application.case_owner]
    else:
        contacts = get_application_contacts(application)

    context = {
        "variation_request": variation_request,
        "application": application,
        "subject": subject,
    }
    template_name = f"email/application/variation_request/{description.lower()}.html"
    send_html_email(template_name, context, contacts)


def send_application_update_response_email(application: ImpOrExp) -> None:
    subject = f"Application Update Response - {application.reference}"
    template_name = "email/application/update/response.html"
    contacts = [application.case_owner]
    context = {
        "application": application,
        "subject": subject,
    }
    send_html_email(template_name, context, contacts)
