from collections.abc import Collection

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from config.celery import app

from . import utils


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
