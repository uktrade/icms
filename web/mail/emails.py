from web.models import AccessRequest

from .messages import AccessRequestEmail
from .recipients import get_ilb_case_officers_email_addresses


def send_access_requested_email(access_request: AccessRequest) -> None:
    recipients = get_ilb_case_officers_email_addresses()
    for recipient in recipients:
        email = AccessRequestEmail(access_request=access_request, to=[recipient])
        email.send()
