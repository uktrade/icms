import itertools

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.mail.message import EmailMultiAlternatives

from web.domains.user.models import AlternativeEmail, PersonalEmail


def send_email(subject, message, recipients, html_message=None, cc_list=None):
    """Sends emails to given recipients. cc_list: ";" separated email list"""
    if cc_list:
        cc_list = ",".join(cc_list.split(";"))

    email = EmailMultiAlternatives(
        subject=subject, body=message, from_email=settings.EMAIL_FROM, to=recipients
    )
    if html_message:
        email.attach_alternative(html_message, "text/html")

    email.send()


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


def get_case_officers_emails():
    """Return a list of emails for import case officers"""
    return list(
        Permission.objects.get(codename="reference_data_access").user_set.values_list(
            "email", flat=True
        )
    )
