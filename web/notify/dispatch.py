import base64

import structlog as logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from markdownify import markdownify
from notifications_python_client.notifications import NotificationsAPIClient

logger = logging.getLogger(__name__)


def get_email_class():
    if settings.SEND_EMAILS:
        return EmailGovNotify
    return EmailMultiAlternatives


class EmailGovNotify:
    def __init__(
        self,
        subject="",
        body="",
        from_email=None,
        to=None,
        cc=None,
        attachments=None,
        **kwargs,
    ):
        self.subject = subject
        self.body = body
        self.from_email = from_email
        self.to = self.get_to(to)
        self.attachments = attachments

    def get_to(self, to):
        return settings.SEND_ALL_EMAILS_TO

    def attach_alternative(self, msg, content_type):
        if content_type == "text/html":
            self.body = markdownify(msg)

    def send(self):
        notifications_client = NotificationsAPIClient(settings.GOV_NOTIFY_API_KEY)
        for recipient in self.to:
            response = notifications_client.send_email_notification(
                email_address=recipient,
                template_id="7b1cf255-d620-43ef-b8e0-8caf38746f87",
                personalisation={
                    "subject": self.subject,
                    "body": self.body,
                    "link_to_file": self.get_attachment(),
                },
            )
            logger.debug(response)

    def get_attachment(self):
        if self.attachments:
            # Only adds the first attachment to test the process
            contents = self.attachments[0][1]
            return {
                "file": base64.b64encode(contents).decode("ascii"),
                "is_csv": False,
                "confirm_email_before_download": None,
                "retention_period": "1 week",
            }
        return {}
