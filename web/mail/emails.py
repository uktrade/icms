from web.domains.case.types import ImpAccessOrExpAccess

from .messages import AccessRequestClosedEmail, AccessRequestEmail
from .recipients import (
    get_email_addresses_for_users,
    get_ilb_case_officers_email_addresses,
)


def send_access_requested_email(access_request: ImpAccessOrExpAccess) -> None:
    recipients = get_ilb_case_officers_email_addresses()
    for recipient in recipients:
        email = AccessRequestEmail(access_request=access_request, to=[recipient])
        email.send()


def send_access_request_closed_email(access_request: ImpAccessOrExpAccess) -> None:
    recipients = get_email_addresses_for_users([access_request.submitted_by])
    for recipient in recipients:
        email = AccessRequestClosedEmail(access_request=access_request, to=[recipient])
        email.send()
