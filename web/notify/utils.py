import itertools

from django.conf import settings
from django.db.models import QuerySet
from django.template.loader import render_to_string

from web.domains.case.types import ImpOrExp
from web.domains.template.utils import get_email_template_subject_body
from web.models import AlternativeEmail, CaseEmail, PersonalEmail


def get_user_emails_by_ids(user_ids):
    """Return a list emails for given users' ids"""
    personal = (
        PersonalEmail.objects.filter(user_id__in=user_ids)
        .filter(portal_notifications=True)
        .values_list("email", flat=True)
    )
    alternative = (
        AlternativeEmail.objects.filter(user_id__in=user_ids)
        .filter(portal_notifications=True)
        .values_list("email", flat=True)
    )
    queryset = personal.union(alternative)
    return list(queryset.all())


def get_notification_emails(user):
    """Returns user's personal and alternative email addresses
    with portal notifications enabled"""
    emails = []
    personal = user.personal_emails.filter(portal_notifications=True)
    alternative = user.alternative_emails.filter(portal_notifications=True)

    for email in itertools.chain(personal, alternative):
        if email.email and email.email not in emails:
            emails.append(email.email)

    return emails


def create_case_email(
    application: ImpOrExp,
    template_code: str,
    to: str | None = None,
    cc: list[str] | None = None,
    attachments: QuerySet | None = None,
) -> CaseEmail:
    subject, body = get_email_template_subject_body(application, template_code)

    case_email = CaseEmail.objects.create(
        subject=subject,
        body=body,
        to=to,
        cc_address_list=cc,
    )

    if attachments:
        case_email.attachments.add(*attachments)

    return case_email


def render_email(template, context):
    """Adds shared variables into context and renders the email"""
    context = context or {}
    context["url"] = settings.DEFAULT_DOMAIN
    context["contact_email"] = settings.ILB_CONTACT_EMAIL
    context["contact_phone"] = settings.ILB_CONTACT_PHONE
    return render_to_string(template, context)
