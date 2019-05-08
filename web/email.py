from django.conf import settings
from django.core.mail import send_mail
from .models import OutboundEmail, EmailAttachment
import logging
import traceback
import html2text

logger = logging.getLogger(__name__)


def send(subject, recipient, html_message):
    """
    Sends email to a single recipient
    Message must be html, html is converted to text both formats are sent
    as a multipart email.

    This function will not throw any exceptions, emails are stored
    with status to be found in OutboundEmail table
    """

    message_text = html2text.html2text(html_message)
    logger.debug('Email to %s:\n subject:%s message:\n%s', recipient, subject,
                 message_text)
    if not settings.AWS_ACCESS_KEY_ID:
        return

    mail = OutboundEmail(to_email=recipient, subject=subject)
    mail.save()
    attachment = EmailAttachment(
        mail=mail, filename='body', mimetype='text/html')
    attachment.save()
    try:
        send_mail(
            subject,
            message_text,
            settings.EMAIL_FROM, [
                recipient,
            ],
            html_message=html_message)
        mail.status = OutboundEmail.SENT
    except Exception:
        logger.error(traceback.format_exc())
        mail.status = OutboundEmail.FAILED
    finally:
        mail.save()
