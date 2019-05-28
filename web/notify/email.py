from django.conf import settings
from django.core.mail import send_mail
from web.models import OutboundEmail, EmailAttachment
import logging
import traceback
import html2text

logger = logging.getLogger(__name__)


def send(subject, to_user, html_message):
    """
    Sends email to a single recipient
    Message must be html, html is converted to text both formats are sent
    as a multipart email.

    This function will not throw any exceptions, emails are stored
    with status to be found in OutboundEmail table
    """

    message_text = html2text.html2text(html_message)
    email_addresses = to_user.personal_emails.filter(portal_notifications=True)
    for email in email_addresses:
        logger.debug('Email to %s:\nsubject:%s\nmessage:\n%s', email.email,
                     subject, message_text)
        mail = OutboundEmail(
            to_email=email.email,
            to_name=to_user.first_name + '' + to_user.last_name,
            subject=subject)
        mail.save()
        attachment = EmailAttachment(
            mail=mail,
            filename='body',
            mimetype='text/html',
            text_attachment=html_message)
        attachment.save()
        try:
            send_mail(
                subject,
                message_text,
                settings.EMAIL_FROM, [email.email],
                html_message=html_message)
            mail.status = OutboundEmail.SENT
        except Exception:
            logger.error(traceback.format_exc())
            mail.status = OutboundEmail.FAILED
        finally:
            mail.save()
