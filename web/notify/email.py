from collections.abc import Collection
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from config.celery import app
from web.models import Exporter, Importer, User
from web.permissions.perms import ExporterObjectPermissions, ImporterObjectPermissions

from . import utils

if TYPE_CHECKING:
    from web.domains.case.types import ImpOrExp


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

    # Importer organisation
    for user in utils.get_importer_contacts(
        importer, ImporterObjectPermissions.is_contact.codename
    ):
        send_email.delay(
            subject, message, utils.get_notification_emails(user), html_message=html_message
        )


def send_to_all_importers(subject: str, message: str, html_message: str | None = None) -> None:
    importers = Importer.objects.filter(is_active=True)
    for importer in importers:
        send_to_importer_contacts(importer, subject, message, html_message)


def send_to_exporter_contacts(
    exporter: Exporter, subject: str, message: str, html_message: str | None = None
) -> None:
    for user in utils.get_exporter_contacts(
        exporter, ExporterObjectPermissions.is_contact.codename
    ):
        send_email.delay(
            subject, message, utils.get_notification_emails(user), html_message=html_message
        )


def send_to_all_exporters(subject: str, message: str, html_message: str | None = None) -> None:
    exporters = Exporter.objects.filter(is_active=True)
    for exporter in exporters:
        send_to_exporter_contacts(exporter, subject, message, html_message)


def send_to_application_contacts(
    application: "ImpOrExp", subject: str, message: str, html_message: str | None = None
) -> None:
    if application.is_import_application():
        users = utils.get_importer_contacts(application.importer)
    else:
        users = utils.get_exporter_contacts(application.exporter)

    for user in users:
        send_email.delay(
            subject, message, utils.get_notification_emails(user), html_message=html_message
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
