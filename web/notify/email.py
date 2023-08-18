from collections.abc import Collection
from typing import Any

import html2text
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import QuerySet
from django.utils import timezone

from config.celery import app
from web.domains.case.types import ImpOrExp
from web.domains.template.utils import get_email_template_subject_body
from web.flow.models import ProcessTypes
from web.models import (
    CaseEmail,
    Exporter,
    Importer,
    User,
    VariationRequest,
    WithdrawApplication,
)
from web.permissions import (
    get_case_officers_for_process_type,
    get_ilb_case_officers,
    get_org_obj_permissions,
    organisation_get_contacts,
)

from . import utils
from .constants import DatabaseEmailTemplate, VariationRequestDescription


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


def send_approval_request_completed_email() -> None:
    context = {"subject": "Access Request Approval Response"}
    template = "email/access/approval/completed.html"
    send_html_email(template, context, get_ilb_case_officers())


def send_approval_request_opened_email(approval_request) -> None:
    entity = (
        "exporter"
        if approval_request.access_request.process_type == ProcessTypes.EAR
        else "importer"
    )
    user_type = "agent" if approval_request.access_request.is_agent_request else "user"
    org = approval_request.access_request.get_specific_model().link
    context = {
        "subject": "Access Request Approval",
        "user_type": user_type,
    }
    contacts = get_organisation_contacts(org)
    template = f"email/access/approval/{entity}/opened.html"
    send_html_email(template, context, contacts)


def send_reassign_email(application: ImpOrExp, comment: str) -> None:
    context = {
        "subject": f"ICMS Case Ref. {application.reference} has been assigned to you",
        "comment": comment,
        "reference": application.reference,
    }
    send_html_email(
        "email/application/reassigned.html",
        context,
        [application.case_owner],
    )


def send_html_email(
    template: str,
    context: dict[str, Any],
    contacts: list[User],
) -> None:
    message_html = utils.render_email(template, context)
    message_text = html2text.html2text(message_html)
    send_to_contacts(context["subject"], message_text, contacts, message_html)


def get_withdrawal_email_subject(withdrawal: WithdrawApplication, application: ImpOrExp) -> str:
    status = ""
    if withdrawal.status == WithdrawApplication.Statuses.DELETED:
        status = " Cancelled"
    elif withdrawal.status != WithdrawApplication.Statuses.OPEN:
        status = " " + withdrawal.get_status_display().title()
    return f"Withdrawal Request{status}: {application.reference}"


def send_withdrawal_email(withdrawal: WithdrawApplication) -> None:
    if withdrawal.status not in WithdrawApplication.Statuses:
        raise ValueError(f"Unsupported Withdrawal Application Status: {withdrawal.status}")

    application = withdrawal.export_application or withdrawal.import_application

    if withdrawal.status in [
        WithdrawApplication.Statuses.OPEN,
        WithdrawApplication.Statuses.DELETED,
    ]:
        contacts = get_case_officers_for_process_type(application.process_type)
    else:
        contacts = get_application_contacts(application)

    subject = get_withdrawal_email_subject(withdrawal, application)

    context = {
        "withdrawal_reason": withdrawal.response,
        "subject": subject,
        "application": application,
    }
    template_name = f"email/application/withdraw/{withdrawal.status}.html"
    send_html_email(template_name, context, list(contacts))


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


def send_database_email(application: ImpOrExp, template_name: DatabaseEmailTemplate) -> None:
    subject, body = get_email_template_subject_body(application, template_name)
    send_to_application_contacts(application, subject, body)
