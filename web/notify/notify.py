from typing import Any

import html2text
import structlog as logging
from django.conf import settings

from web.domains.case.services import document_pack
from web.mail.recipients import get_notification_emails
from web.models import DFLApplication

from . import email, utils

logger = logging.getLogger(__name__)


def send_notification(
    subject: str,
    template: str,
    context: dict[str, Any] | None = None,
    recipients: list[str] | None = None,
    cc_list: list[str] | None = None,
    attachment_ids: tuple[int, ...] = (),
):
    """Renders given email template and sends to recipients.

    User's personal and alternative emails with portal notifications
    enabled will be used.

    Emails are queued to Redis to be sent asynchronously"""

    html_message = utils.render_email(template, context)
    message_text = html2text.html2text(html_message)
    email.send_email.delay(
        subject,
        message_text,
        recipients,
        html_message=html_message,
        cc=cc_list,
        attachment_ids=attachment_ids,
    )


def register(user, password):
    subject = "Import Case Management System Account"
    send_notification(
        subject,
        "email/registration/registration.html",
        context={
            "password": password,
            "username": user.username,
            "name": user.full_name,
            "first_name": user.first_name,
        },
        recipients=get_notification_emails(user),
    )


def send_constabulary_deactivated_firearms_notification(application: DFLApplication) -> None:
    subject = "Automatic Notification: Deactivated Firearm Licence Authorised"
    template = "email/import/constabulary_notification.html"
    context = {"subject": subject, "ilb_email": settings.ILB_CONTACT_EMAIL}

    html_message = utils.render_email(template, context)
    body = html2text.html2text(html_message)
    recipients = [application.constabulary.email]
    doc_pack = document_pack.pack_active_get(application)
    attachment_ids = tuple(doc_pack.document_references.values_list("document__id", flat=True))

    email.send_email.delay(
        subject, body, recipients, attachment_ids=attachment_ids, html_message=html_message
    )
