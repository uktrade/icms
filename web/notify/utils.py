#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools

from django.conf import settings
from django.core.mail import send_mail

from web.domains.team.models import Role
from web.domains.user.models import AlternativeEmail, PersonalEmail, User


def send_email(
    subject, message, recipients, html_message=None,
):
    """
        Sends emails to given recipients.
    """
    send_mail(subject, message, settings.EMAIL_FROM, recipients, html_message=html_message)


def get_role_member_notification_emails(role):
    """
        Return a list of emails for all active members of given role
        with portal notifications enabled
    """
    user_ids = role.user_set.filter(account_status=User.ACTIVE).values_list("id", flat=True)
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
    """
        Returns user's personal and alternative email addresses
        with portal notifications enabled
    """
    emails = []
    personal = user.personal_emails.filter(portal_notifications=True)
    alternative = user.alternative_emails.filter(portal_notifications=True)

    for email in itertools.chain(personal, alternative):
        if email.email and email.email not in emails:
            emails.append(email.email)

    return emails


def get_import_case_officers_emails():
    """
        Return a list of emails for import case officers
    """
    return get_role_member_notification_emails(
        Role.objects.get(name="ILB Case Officers:Import Application Case Officer")
    )


def get_export_case_officers_emails():
    """
        Return a list of emails for export case officers
    """
    return get_role_member_notification_emails(
        Role.objects.get(name="ILB Case Officers:Certificate Application Case Officer")
    )


def get_app_url(request):
    """
        Returns app's base url with scheme and host
        e.g. http://example.com[:port]
    """
    return "{0}://{1}".format(request.scheme, request.get_host())
