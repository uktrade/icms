from collections.abc import Iterable

from django.db.models import QuerySet

from web.domains.case.types import ImpOrExp, Organisation
from web.flow.models import ProcessTypes
from web.models import CaseEmail, User
from web.notify.utils import get_notification_emails
from web.permissions import (
    get_all_case_officers,
    get_ilb_case_officers,
    get_org_obj_permissions,
    organisation_get_contacts,
)

from .decorators import override_recipients


def get_application_contacts(application: ImpOrExp) -> QuerySet[User]:
    if application.is_import_application():
        org = application.agent or application.importer
    else:
        org = application.agent or application.exporter
    return get_organisation_contacts(org)


def get_organisation_contacts(org):
    obj_perms = get_org_obj_permissions(org)
    return organisation_get_contacts(org, perms=[obj_perms.edit.codename])


def get_all_case_officers_email_addresses() -> list[str]:
    users = get_all_case_officers()
    return get_email_addresses_for_users(users)


def get_ilb_case_officers_email_addresses() -> list[str]:
    users = get_ilb_case_officers()
    return get_email_addresses_for_users(users)


def get_case_officers_email_addresses(process_type: ProcessTypes) -> list[str]:
    match process_type:
        case ProcessTypes.SANCTIONS:
            return get_all_case_officers_email_addresses()
        case _:
            return get_ilb_case_officers_email_addresses()


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


@override_recipients
def get_email_addresses_for_case_email(case_email: CaseEmail) -> list[str]:
    recipients = case_email.cc_address_list or []
    if case_email.to:
        recipients.append(case_email.to)
    return list(set(recipients))
