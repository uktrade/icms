import structlog as logging
from django.template.loader import render_to_string

import html2text

from . import email, utils

# Get an instance of a logger
logger = logging.getLogger(__name__)


def send_notification(subject, template, context={}, recipients=[]):
    """
        Renders given email template and sends to recipiens.
        User's personal and alternative emails with portal notifications
        enabled will be used.

        Emails are queued to Redis to be sent asynchronously
    """
    html_message = render_to_string(template, context)
    message_text = html2text.html2text(html_message)
    email.send_email.delay(subject, message_text, recipients, html_message)


def register(request, user, password):
    logger.debug('Notifying user for registration', user=user)
    subject = 'Import Case Management System Account'
    send_notification(subject,
                      'email/registration/registration.html',
                      context={
                          'password': password,
                          'username': user.username,
                          'name': user.full_name,
                          'first_name': user.first_name,
                          'url': utils.get_app_url(request)
                      },
                      recipients=utils.get_notification_emails(user))


def access_request_admin(user, access_request):
    logger.debug('Notifying admins for new access request',
                 user=user,
                 access_request=access_request)
    subject = 'Import Case Management System Account'
    send_notification(subject,
                      'email/access/admin.html',
                      context={
                          'subject': subject,
                          'user': user,
                          'access_request': access_request
                      },
                      recipients=utils.get_notification_emails(user))


def access_request_requester(access_request):
    logger.debug('Notifying user for new access request',
                 access_request=access_request)
    requester = access_request.submitted_by
    subject = 'Import Case Management System Account'
    send_notification(subject,
                      'email/access/requester.html',
                      context={
                          'subject': subject,
                          'user': requester,
                          'access_request': access_request
                      },
                      recipients=utils.get_notification_emails(requester))


def mailshot(request, mailshot):
    logger.debug('Notifying for published mailshot', mailshot=mailshot)
    html_message = render_to_string(
        'email/mailshot/mailshot.html', {
            'subject': mailshot.email_subject,
            'body': mailshot.email_body,
            'url': utils.get_app_url(request)
        })
    message_text = html2text.html2text(html_message)
    email.send_mailshot.delay(f'{mailshot.email_subject}',
                              message_text,
                              html_message=html_message,
                              to_importers=mailshot.is_to_importers,
                              to_exporters=mailshot.is_to_exporters)


def retract_mailshot(request, mailshot):
    logger.debug('Notifying for retracted mailshot', mailshot=mailshot)
    html_message = render_to_string(
        'email/mailshot/mailshot.html', {
            'subject': mailshot.retract_email_subject,
            'body': mailshot.retract_email_body,
            'url': utils.get_app_url(request)
        })
    message_text = html2text.html2text(html_message)
    email.send_mailshot.delay(f'{mailshot.retract_email_subject}',
                              message_text,
                              html_message=html_message,
                              to_importers=mailshot.is_to_importers,
                              to_exporters=mailshot.is_to_exporters)
