import datetime as dt
from typing import Literal

import html2text
import structlog as logging
from django.contrib.postgres.aggregates import StringAgg
from django.utils import timezone

from config.celery import app
from web.auth.utils import get_ilb_admin_users
from web.models import (
    Constabulary,
    FirearmsAuthority,
    Importer,
    Section5Authority,
    User,
)
from web.permissions import SysPerms

from . import email, utils

logger = logging.getLogger(__name__)


def send_notification(subject, template, context=None, recipients=None, cc_list=None):
    """Renders given email template and sends to recipients.

    User's personal and alternative emails with portal notifications
    enabled will be used.

    Emails are queued to Redis to be sent asynchronously"""

    html_message = utils.render_email(template, context)
    message_text = html2text.html2text(html_message)
    email.send_email.delay(subject, message_text, recipients, html_message=html_message, cc=cc_list)


def send_case_officer_notification(subject, template, context=None):
    """Renders given email template and sends to case officers."""
    html_message = utils.render_email(template, context)
    message_text = html2text.html2text(html_message)
    email.send_to_contacts(subject, message_text, get_ilb_admin_users(), html_message)


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
    html_message = utils.render_email(
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
    html_message = utils.render_email(
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
        cc_list=fir.email_cc_address_list,
    )


def further_information_responded(process, fir):
    send_case_officer_notification(
        # TODO: use case reference instead of pk
        f"FIR Response - {process.pk} - {fir.request_subject}",
        "email/fir/responded.html",
        context={"process": process, "fir": fir},
    )


@app.task(name="web.notify.notify.send_firearms_authority_expiry_notification")
def send_firearms_authority_expiry_notification() -> None:
    """Sends a notification to constabulary contacts verified firearms authority editors for verified firearms
    authorities that expire in 30 days"""

    logger.info("Running firearms authority expiry notification task")

    expiry_date = timezone.now().date() + dt.timedelta(days=30)
    expiry_date_str = expiry_date.strftime("%-d %B %Y")
    subject = f"Verified Firearms Authorities Expiring {expiry_date_str}"

    constabularies = Constabulary.objects.filter(
        firearmsauthority__end_date=expiry_date, is_active=True
    ).distinct()

    recipient_users = User.objects.filter(
        groups__permissions__codename=SysPerms.edit_firearm_authorities.codename
    )

    # TODO ICMSLST-1937 Update recipients to be constabulary contacts instead of all users with authority editing permission
    # Send emails to users who can edit firearms authorities for a specific constabulary (recipeint_users query into for loop)

    for constabulary in constabularies:
        importers = (
            Importer.objects.filter(
                firearms_authorities__issuing_constabulary=constabulary,
                firearms_authorities__end_date=expiry_date,
                is_active=True,
            )
            .annotate(
                authority_refs=StringAgg(
                    "firearms_authorities__reference",
                    delimiter=", ",
                    ordering="firearms_authorities__reference",
                )
            )
            .order_by("name")
        )

        for user in recipient_users:
            send_notification(
                subject,
                "email/import/authority_expiring.html",
                context={
                    "section_5": False,
                    "expiry_date": expiry_date_str,
                    "constabulary_name": constabulary.name,
                    "importers": importers,
                    "subject": subject,
                },
                recipients=utils.get_notification_emails(user),
            )

    logger.info(
        f"Firearms authority expiry notifications sent to {constabularies.count()} constabulary's contacts"
    )


@app.task(name="web.notify.notify.send_section_5_expiry_notification")
def send_section_5_expiry_notification() -> None:
    """Sends a notification to all verified section 5 authority editors for verified section 5 authorities
    that expire in 30 days"""

    logger.info("Running section 5 authority expiry notification task")

    expiry_date = timezone.now().date() + dt.timedelta(days=30)
    expiry_date_str = expiry_date.strftime("%-d %B %Y")
    subject = f"Verified Section 5 Authorities Expiring {expiry_date_str}"

    importers = (
        Importer.objects.filter(
            section5_authorities__end_date=expiry_date,
            is_active=True,
        )
        .annotate(
            authority_refs=StringAgg(
                "section5_authorities__reference",
                delimiter=", ",
                ordering="section5_authorities__reference",
            )
        )
        .order_by("name")
    )

    recipient_users = User.objects.filter(
        groups__permissions__codename=SysPerms.edit_section_5_firearm_authorities.codename
    )

    for user in recipient_users:
        send_notification(
            subject,
            "email/import/authority_expiring.html",
            context={
                "expiry_date": expiry_date_str,
                "section_5": True,
                "importers": importers,
                "subject": subject,
            },
            recipients=utils.get_notification_emails(user),
        )

    logger.info(
        f"Section 5 authority expiry notifications sent to {importers.count()} importers contacts"
    )


def authority_archived_notification(
    authority: FirearmsAuthority | Section5Authority,
    authority_type: Literal["Firearms", "Section 5"],
) -> None:
    """Sends a notification to all importer maintainers when a verified authority is archived"""

    archived_date = timezone.now().strftime("%-d %B %Y")
    subject = f"Importer {authority.importer.id} Verified {authority_type} Authority {authority.reference} Archived {archived_date}"

    recipient_users = User.objects.filter(groups__permissions__codename=SysPerms.ilb_admin.codename)

    for user in recipient_users:
        send_notification(
            subject,
            "email/import/authority_archived.html",
            context={
                "authority_type": authority_type,
                "authority": authority,
                "subject": subject,
            },
            recipients=utils.get_notification_emails(user),
        )
