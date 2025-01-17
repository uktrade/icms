import logging
from urllib.parse import ParseResult, urlparse
from uuid import UUID

from django.contrib.sites.models import Site
from django.core.mail.backends.base import BaseEmailBackend

from web.domains.user.utils import send_and_create_email_verification
from web.mail.constants import EmailTypes
from web.mail.models import EmailTemplate
from web.models import Email

from .api import send_email
from .messages import GOVNotifyEmailMessage

logger = logging.getLogger(__name__)


class GovNotifyEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages: list[GOVNotifyEmailMessage]) -> None:
        for message in email_messages:
            for recipient in message.recipients():
                logger.info("Sending %s email to %s", message.name.label, recipient)
                self._send_message(message.template_id, message.get_personalisation(), recipient)

    def _send_message(self, template_id: UUID, personalisation: dict, recipient: str) -> None:
        self._verify_recipient(template_id, personalisation, recipient)

        send_email.apply_async(args=[template_id, personalisation, recipient])

    def _verify_recipient(self, template_id: UUID, personalisation: dict, recipient: str) -> None:
        """Checks if the supplied email address has been verified."""

        template = EmailTemplate.objects.get(gov_notify_template_id=template_id)

        # Do not perform logic if email being sent is an email verify email
        if template.name == EmailTypes.EMAIL_VERIFICATION:
            logger.debug(
                "GovNotifyEmailBackend._verify_recipient: Not verifying EMAIL_VERIFICATION email."
            )
            return

        email = Email.objects.filter(email__iexact=recipient).first()
        if email and not email.is_verified:
            if icms_url := personalisation.get("icms_url"):
                result: ParseResult = urlparse(icms_url)
                try:
                    site = Site.objects.get(domain=result.netloc)
                    send_and_create_email_verification(email, site)
                except Site.DoesNotExist:
                    logger.error(
                        f"GovNotifyEmailBackend._verify_recipient: Unable to load site from icms url: {icms_url}"
                    )
            else:
                logger.error(
                    f"GovNotifyEmailBackend._verify_recipient: Unable to send very email for email_pk: {email.pk}"
                )
