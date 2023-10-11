from collections.abc import Collection
from typing import Any

import html2text
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import QuerySet

from config.celery import app
from web.domains.case.types import ImpOrExp
from web.models import Exporter, Importer, User
from web.permissions import get_org_obj_permissions, organisation_get_contacts

from . import utils


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
    """Sends mailshot emails.

    Used in two places:
        web/notify/notify.py -> def mailshot
        web/notify/notify.py -> def retract_mailshot

    The html message is derived from a template, but they are editable by the ILB Team
    on a per-mailshot basis.
    The two template codes to search for are as follows:
      - PUBLISH_MAILSHOT
      - RETRACT_MAILSHOT

    The mailshot detail view the applicant will see in the workbasket includes the files
    therefore we won't need to include them in the email sent via GOV.UK Notify.
    """

    # Note: Decided to send mailshots to all org contacts.
    # Previously it only sent them to contacts with edit permission.
    if to_importers:
        importers = Importer.objects.filter(is_active=True)

        for importer in importers:
            contacts = organisation_get_contacts(importer)
            send_to_contacts(subject, message, contacts, html_message)

    if to_exporters:
        exporters = Exporter.objects.filter(is_active=True)

        for exporter in exporters:
            contacts = organisation_get_contacts(exporter)
            send_to_contacts(subject, message, contacts, html_message)


def send_html_email(
    template: str,
    context: dict[str, Any],
    contacts: list[User],
) -> None:
    message_html = utils.render_email(template, context)
    message_text = html2text.html2text(message_html)
    send_to_contacts(context["subject"], message_text, contacts, message_html)


def send_application_update_response_email(application: ImpOrExp) -> None:
    subject = f"Application Update Response - {application.reference}"
    template_name = "email/application/update/response.html"
    contacts = [application.case_owner]
    context = {
        "application": application,
        "subject": subject,
    }
    send_html_email(template_name, context, contacts)
