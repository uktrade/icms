import html2text
from django.conf import settings
from django.template.loader import render_to_string

from . import email, utils


def _render_email(template, context):
    """Adds shared variables into context and renders the email"""
    context = context or {}
    context["url"] = settings.DEFAULT_DOMAIN
    context["contact_email"] = settings.ILB_CONTACT_EMAIL
    context["contact_phone"] = settings.ILB_CONTACT_PHONE
    return render_to_string(template, context)


def send_notification(subject, template, context=None, recipients=None, cc_list=None):
    """Renders given email template and sends to recipients.

    User's personal and alternative emails with portal notifications
    enabled will be used.

    Emails are queued to Redis to be sent asynchronously"""

    html_message = _render_email(template, context)
    message_text = html2text.html2text(html_message)
    email.send_email.delay(subject, message_text, recipients, html_message=html_message, cc=cc_list)


def send_case_officer_notification(subject, template, context=None):
    """Renders given email template and sends to case officers."""
    html_message = _render_email(template, context)
    message_text = html2text.html2text(html_message)
    email.send_to_case_officers.delay(subject, message_text, html_message)


def update_request(subject, content, contacts, cc_list):
    # TODO: investigate web.notify.utils.get_notification_emails
    recipients = [contact.email for contact in contacts]
    email.send_email.delay(subject, content, recipients, cc=cc_list)


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
        recipients=utils.get_notification_emails(user),
    )


def access_requested_importer(case_reference):
    # TODO: Generate access request reference when created. Currently empty
    subject = f"Access Request {case_reference}"
    send_case_officer_notification(
        subject, "email/access/access_requested.html", context={"subject": subject}
    )


def access_requested_exporter(case_reference):
    subject = f"Access Request {case_reference}"
    send_case_officer_notification(
        subject, "email/access/access_requested.html", context={"subject": subject}
    )


def access_request_closed(access_request):
    requester = access_request.submitted_by
    subject = "Import Case Management System Account"
    send_notification(
        subject,
        "email/access/access_request_closed.html",
        context={"subject": subject, "access_request": access_request},
        recipients=utils.get_notification_emails(requester),
    )


def mailshot(mailshot):
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
    html_message = _render_email(
        "email/mailshot/mailshot.html",
        {
            "subject": mailshot.retract_email_subject,
            "body": mailshot.retract_email_body,
        },
    )
    message_text = html2text.html2text(html_message)
    email.send_mailshot.delay(
        f"{mailshot.retract_email_subject}",
        message_text,
        html_message=html_message,
        to_importers=mailshot.is_to_importers,
        to_exporters=mailshot.is_to_exporters,
    )


def further_information_requested(fir, contacts):
    send_notification(
        f"{fir.request_subject}",
        "email/fir/requested.html",
        context={"subject": fir.request_subject, "request_detail": fir.request_detail},
        # TODO: investigate web.notify.utils.get_notification_emails
        recipients=[contact.email for contact in contacts],
        cc_list=fir.email_cc_address_list or [],
    )


def further_information_responded(process, fir):
    send_case_officer_notification(
        # TODO: use case reference instead of pk
        f"FIR Response - {process.pk} - {fir.request_subject}",
        "email/fir/responded.html",
        context={"process": process, "fir": fir},
    )
