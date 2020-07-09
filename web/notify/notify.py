import html2text
import structlog as logging
from django.conf import settings
from django.template.loader import render_to_string

from . import email, utils

# Get an instance of a logger
logger = logging.getLogger(__name__)


def _render_email(template, context):
    """
        Adds shared variables into context and renders the email
    """
    context["url"] = settings.DEFAULT_DOMAIN
    return render_to_string(template, context)


def send_notification(subject, template, context={}, recipients=[]):
    """
        Renders given email template and sends to recipiens.
        User's personal and alternative emails with portal notifications
        enabled will be used.

        Emails are queued to Redis to be sent asynchronously
    """
    html_message = _render_email(template, context)
    message_text = html2text.html2text(html_message)
    email.send_email.delay(subject, message_text, recipients, html_message)


def register(user, password):
    logger.debug("Notifying user for registration", user=user)
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
        recipients=utils.get_notification_emails(user),
    )


def access_requested(access_request):
    logger.debug("Notifying case officers for new access request", access_request=access_request)
    subject = f"Access Request {access_request.id}"
    html_message = _render_email("email/access/access_requested.html", context={"subject": subject})
    message_text = html2text.html2text(html_message)
    if access_request.is_importer():
        email.send_to_import_case_officers.delay(subject, message_text, html_message)
    else:
        email.send_to_export_case_officers.delay(subject, message_text, html_message)


def access_request_closed(access_request):
    logger.debug("Notify user their access request is closed", access_request=access_request)
    requester = access_request.submitted_by
    subject = "Import Case Management System Account"
    send_notification(
        subject,
        "email/access/access_request_closed.html",
        context={"subject": subject, "access_request": access_request},
        recipients=utils.get_notification_emails(requester),
    )


def mailshot(mailshot):
    logger.debug("Notifying for published mailshot", mailshot=mailshot)
    html_message = _render_email(
        "email/mailshot/mailshot.html",
        {"subject": mailshot.email_subject, "body": mailshot.email_body},
    )
    message_text = html2text.html2text(html_message)
    email.send_mailshot.delay(
        f"{mailshot.email_subject}",
        message_text,
        html_message=html_message,
        to_importers=mailshot.is_to_importers,
        to_exporters=mailshot.is_to_exporters,
    )


def retract_mailshot(mailshot):
    logger.debug("Notifying for retracted mailshot", mailshot=mailshot)
    html_message = _render_email(
        "email/mailshot/mailshot.html",
        {"subject": mailshot.retract_email_subject, "body": mailshot.retract_email_body,},
    )
    message_text = html2text.html2text(html_message)
    email.send_mailshot.delay(
        f"{mailshot.retract_email_subject}",
        message_text,
        html_message=html_message,
        to_importers=mailshot.is_to_importers,
        to_exporters=mailshot.is_to_exporters,
    )
