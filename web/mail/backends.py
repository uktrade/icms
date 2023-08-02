from uuid import UUID

import structlog as logging
from django.core.mail.backends.base import BaseEmailBackend

from web.mail.api import send_email
from web.mail.messages import GOVNotifyEmailMessage

logger = logging.getLogger(__name__)


class GovNotifyEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages: list[GOVNotifyEmailMessage]) -> None:
        for message in email_messages:
            for recipient in message.recipients():
                logger.info("Sending %s email to %s", message.name.label, recipient)
                self._send_message(message.template_id, message.personalisation, recipient)

    def _send_message(self, template_id: UUID, personalisation: dict, recipient: str) -> None:
        send_email.delay(template_id, personalisation, recipient)
