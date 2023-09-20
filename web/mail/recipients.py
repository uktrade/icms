from collections.abc import Iterable

from django.db.models import QuerySet

from web.domains.case.types import ImpOrExp, Organisation
from web.flow.models import ProcessTypes
from web.models import CaseEmail, Constabulary, Email, User
from web.permissions import (
    Perms,
    SysPerms,
    constabulary_get_contacts,
    get_all_case_officers,
    get_ilb_case_officers,
    get_org_obj_permissions,
    organisation_get_contacts,
)

from .decorators import override_recipients


def get_user_emails_by_ids(user_ids: list[int]) -> list[str]:
    """Return a list emails for given users' ids"""
    return list(
        Email.objects.filter(user_id__in=user_ids)
        .filter(portal_notifications=True)
        .values_list("email", flat=True)
        .distinct()
        .order_by("email")
    )


def get_notification_emails(user: User) -> list[str]:
    """Returns user's personal and alternative email addresses
    with portal notifications enabled"""
    return get_user_emails_by_ids([user.id])


def get_application_contacts(application: ImpOrExp) -> QuerySet[User]:
    if application.is_import_application():
        org = application.agent or application.importer
    else:
        org = application.agent or application.exporter
    return get_organisation_contacts(org)


def get_organisation_contacts(org) -> QuerySet[User]:
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


def get_email_addresses_for_mailshot(organisation_class: type[Organisation]) -> list[str]:
    emails = []
    for org in organisation_class.objects.filter(is_active=True):
        emails.extend(get_organisation_contact_email_addresses(org))
    return list(set(emails))


def get_email_addresses_for_section_5_expiring_authorities() -> list[str]:
    recipients = User.objects.filter(
        groups__permissions__codename=SysPerms.edit_section_5_firearm_authorities.codename
    )
    return get_email_addresses_for_users(recipients)


def get_email_addresses_for_constabulary(constabulary: Constabulary) -> list[str]:
    recipients = constabulary_get_contacts(
        constabulary, perms=[Perms.obj.constabulary.verified_fa_authority_editor.codename]
    )
    return get_email_addresses_for_users(recipients)


@override_recipients
def get_shared_mailbox_for_constabulary(constabulary: Constabulary) -> list[str]:
    return [constabulary.email]


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
