from collections.abc import Collection

import html2text
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from config.celery import app
from web.domains.case.types import ImpOrExp
from web.models import CaseEmail, Exporter, Importer, User
from web.permissions import get_org_obj_permissions, organisation_get_contacts
from web.utils.s3 import get_file_from_s3, get_s3_client

from . import utils


@app.task(name="web.notify.email.send_email")
def send_email(
    subject: str,
    body: str,
    recipients: Collection[str],
    cc: Collection[str] = (),
    attachments: Collection[tuple[str, bytes]] = (),
    html_message: str | None = None,
):
    message = EmailMultiAlternatives(
        subject, body, settings.EMAIL_FROM, recipients, cc=cc, attachments=attachments
    )

    if html_message:
        message.attach_alternative(html_message, "text/html")

    message.send()


def send_to_importer_contacts(
    importer: Importer, subject: str, message: str, html_message: str | None = None
) -> None:
    if importer.type == Importer.INDIVIDUAL:
        # TODO: ICMSLST-1948 Revisit this (importer.user is something that should be removed.)
        if importer.user and importer.user.account_status == User.ACTIVE:
            send_email.delay(
                subject,
                message,
                utils.get_notification_emails(importer.user),
                html_message=html_message,
            )

        return

    obj_perms = get_org_obj_permissions(importer)
    contacts = organisation_get_contacts(importer, perms=[obj_perms.is_contact.codename])

    # Importer organisation
    for contact in contacts:
        send_email.delay(
            subject, message, utils.get_notification_emails(contact), html_message=html_message
        )


def send_to_all_importers(subject: str, message: str, html_message: str | None = None) -> None:
    importers = Importer.objects.filter(is_active=True)
    for importer in importers:
        send_to_importer_contacts(importer, subject, message, html_message)


def send_to_exporter_contacts(
    exporter: Exporter, subject: str, message: str, html_message: str | None = None
) -> None:
    obj_perms = get_org_obj_permissions(exporter)

    # TODO ICMSLST-1968 is_contact perm deprecated
    contacts = organisation_get_contacts(exporter, perms=[obj_perms.is_contact.codename])

    for contact in contacts:
        send_email.delay(
            subject, message, utils.get_notification_emails(contact), html_message=html_message
        )


def send_to_all_exporters(subject: str, message: str, html_message: str | None = None) -> None:
    exporters = Exporter.objects.filter(is_active=True)
    for exporter in exporters:
        send_to_exporter_contacts(exporter, subject, message, html_message)


def send_to_application_contacts(
    application: ImpOrExp, subject: str, message: str, html_message: str | None = None
) -> None:
    if application.is_import_application():
        org = application.agent or application.importer
    else:
        org = application.agent or application.exporter

    obj_perms = get_org_obj_permissions(org)
    contacts = organisation_get_contacts(org, perms=[obj_perms.edit.codename])

    for contact in contacts:
        send_email.delay(
            subject, message, utils.get_notification_emails(contact), html_message=html_message
        )


@app.task(name="web.notify.email.send_to_case_officers")
def send_to_case_officers(subject, message, html_message=None):
    recipients = utils.get_case_officers_emails()
    send_email.delay(subject, message, recipients, html_message=html_message)


@app.task(name="web.notify.email.send_mailshot")
def send_mailshot(subject, message, html_message=None, to_importers=False, to_exporters=False):
    """
    Sends mailshots
    """
    if to_importers:
        send_to_all_importers(subject, message, html_message=html_message)
    if to_exporters:
        send_to_all_exporters(subject, message, html_message=html_message)


def send_case_email(case_email: CaseEmail) -> None:
    attachments = []
    s3_client = get_s3_client()

    for document in case_email.attachments.all():
        file_content = get_file_from_s3(document.path, client=s3_client)
        attachments.append((document.filename, file_content))

    send_email(
        case_email.subject,
        case_email.body,
        [case_email.to],
        case_email.cc_address_list,
        attachments,
    )

    case_email.status = CaseEmail.Status.OPEN
    case_email.sent_datetime = timezone.now()
    case_email.save()


def send_refused_email(application: ImpOrExp) -> None:
    context = {
        "application": application,
        "subject": f"Application reference {application.reference} has been refused by ILB.",
    }
    template = "email/application/refused.html"
    message_html = utils.render_email(template, context)
    message_text = html2text.html2text(message_html)
    send_to_application_contacts(application, context["subject"], message_text, message_html)
