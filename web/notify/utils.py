#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools

from django.conf import settings
from django.core.mail import send_mail


def send_email(
    subject,
    message,
    recipients,
    html_message=None,
):
    """
        Sends emails to given recipients.
    """
    send_mail(subject,
              message,
              settings.EMAIL_FROM,
              recipients,
              html_message=html_message)


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


def get_app_url(request):
    """
        Returns app's base url with scheme and host
        e.g. http://example.com[:port]
        
    """
    return "{0}://{1}".format(request.scheme, request.get_host())
