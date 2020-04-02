import itertools

import structlog as logging
from django.conf import settings
from django.core.mail import send_mail

import html2text
from config.celery import app

logger = logging.getLogger(__name__)


def _send_email(
    subject,
    message,
    recipients,
    html_message=None,
):
    """
        Sends emails to given recipients emails.
        Emails send tasks are queued to Redis to be sent asynchronously
    """

    send_mail(subject,
              message,
              settings.EMAIL_FROM,
              recipients,
              html_message=html_message)


def _get_user_emails(user):
    emails = []
    personal = user.personal_emails.filter(portal_notifications=True)
    alternative = user.alternative_emails.filter(portal_notifications=True)

    for email in itertools.chain(personal, alternative):
        if email.email and email.email not in emails:
            emails.append(email.email)

    return emails


@app.task(name='web.notify.email.send_email_to_user')
def send_email_to_user(subject, user, html_message):
    message_text = html2text.html2text(html_message)
    emails = _get_user_emails(user)
    _send_email(subject, message_text, emails, html_message=html_message)


def email_user(subject, user, html_message):
    """
    Sends email to a single user. User's personal and alternative emails with
    portal notifications enabled will be used.

    Message must be html, html is converted to text and both formats are sent
    as a multipart email.

    """
    logger.debug('Sending email to user', subject=subject, user=user)
    send_email_to_user.delay(subject, user, html_message)

def email_importers(subject, user)
