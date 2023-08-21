from collections.abc import Iterable

from web.domains.case.types import ImpOrExp, Organisation
from web.models import User
from web.notify.email import get_application_contacts, get_organisation_contacts
from web.notify.utils import get_notification_emails
from web.permissions import get_ilb_case_officers

from .decorators import override_recipients


def get_ilb_case_officers_email_addresses() -> list[str]:
    users = get_ilb_case_officers()
    return get_email_addresses_for_users(users)


def get_application_contact_email_addresses(application: ImpOrExp) -> list[str]:
    users = get_application_contacts(application)
    return get_email_addresses_for_users(users)


def get_organisation_contact_email_addresses(org: Organisation) -> list[str]:
    users = get_organisation_contacts(org)
    return get_email_addresses_for_users(users)


@override_recipients
def get_email_addresses_for_users(users: Iterable[User]) -> list[str]:
    emails = []
    for user in users:
        emails.extend(get_notification_emails(user))
    return list(set(emails))
