import html2text
import structlog as logging
from django.conf import settings
from django.template.loader import render_to_string

from web.domains.exporter.models import Exporter

from . import email, utils

# Get an instance of a logger
logger = logging.getLogger(__name__)


def _render_email(template, context):
    """
        Adds shared variables into context and renders the email
    """
    context = context or {}
    context["url"] = settings.DEFAULT_DOMAIN
    context["contact_email"] = settings.ILB_CONTACT_EMAIL
    context["contact_phone"] = settings.ILB_CONTACT_PHONE
    return render_to_string(template, context)


def send_notification(subject, template, context=None, recipients=None):
    """
        Renders given email template and sends to recipiens.
        User's personal and alternative emails with portal notifications
        enabled will be used.

        Emails are queued to Redis to be sent asynchronously
    """
    html_message = _render_email(template, context)
    message_text = html2text.html2text(html_message)
    email.send_email.delay(subject, message_text, recipients, html_message)


def send_import_case_officer_notification(subject, template, context=None):
    """
        Renders given email template and sends to import case officers.
    """
    html_message = _render_email(template, context)
    message_text = html2text.html2text(html_message)
    email.send_to_import_case_officers.delay(subject, message_text, html_message)


def send_export_case_officer_notification(subject, template, context=None):
    """
        Renders given email template and sends to export case officers.
    """
    html_message = _render_email(template, context)
    message_text = html2text.html2text(html_message)
    email.send_to_export_case_officers.delay(subject, message_text, html_message)


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
    # TODO: Generate access request reference when created. Currently empty
    subject = f"Access Request {access_request.reference}"
    if access_request.is_importer_request():
        send_import_case_officer_notification(
            subject, "email/access/access_requested.html", context={"subject": subject}
        )
    else:
        send_export_case_officer_notification(
            subject, "email/access/access_requested.html", context={"subject": subject}
        )


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


def further_information_requested(fir_process):
    logger.debug("Notifying for new FIR", process=fir_process)
    team = fir_process.parent_process.get_fir_response_team()
    fir = fir_process.fir
    if isinstance(team, Exporter):
        recipients = utils.get_team_member_emails_with_permission(team, "web.IMP_EDIT_APP")
    else:
        recipients = utils.get_team_member_emails_with_permission(
            team, "web.IMP_CERT_EDIT_APPLICATION"
        )

    # TODO: use request_cc_email list too?
    send_notification(
        f"{fir.request_subject}",
        "email/fir/requested.html",
        context={"subject": fir.request_subject, "request_detail": fir.request_detail},
        recipients=recipients,
    )


def further_information_responded(fir_process):
    logger.debug("Notifying case officers for FIR response", process=fir_process)
    team = fir_process.parent_process.get_fir_response_team()
    subject = f"FIR Reponse - {fir_process.parent_display}"
    if isinstance(team, Exporter):
        send_export_case_officer_notification(
            subject, "email/fir/responded.html", context={"process": fir_process}
        )
    else:
        send_import_case_officer_notification(
            subject, "email/fir/responded.html", context={"process": fir_process}
        )
