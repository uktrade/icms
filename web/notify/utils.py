import itertools
from typing import TYPE_CHECKING

from django.contrib.auth.models import Permission

from web.models import AlternativeEmail, PersonalEmail, User
from web.permissions.perms import ExporterObjectPermissions, ImporterObjectPermissions

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from web.models import Exporter, Importer


def get_user_emails_by_ids(user_ids):
    """Return a list emails for given users' ids"""
    personal = (
        PersonalEmail.objects.filter(user_id__in=user_ids)
        .filter(portal_notifications=True)
        .values_list("email", flat=True)
    )
    alternative = (
        AlternativeEmail.objects.filter(user_id__in=user_ids)
        .filter(portal_notifications=True)
        .values_list("email", flat=True)
    )
    queryset = personal.union(alternative)
    return list(queryset.all())


def get_notification_emails(user):
    """Returns user's personal and alternative email addresses
    with portal notifications enabled"""
    emails = []
    personal = user.personal_emails.filter(portal_notifications=True)
    alternative = user.alternative_emails.filter(portal_notifications=True)

    for email in itertools.chain(personal, alternative):
        if email.email and email.email not in emails:
            emails.append(email.email)

    return emails


def get_case_officers_emails():
    """Return a list of emails for import case officers"""
    return list(
        Permission.objects.get(codename="ilb_admin").user_set.values_list("email", flat=True)
    )


def get_importer_contacts(importer: "Importer", permission: str | None = None) -> "QuerySet[User]":
    """Return a queryset of users for an importer with specified permission"""
    if not permission:
        permission = ImporterObjectPermissions.edit.codename

    return User.objects.prefetch_related("importeruserobjectpermission_set").filter(
        importeruserobjectpermission__content_object=importer,
        importeruserobjectpermission__permission__codename=permission,
        account_status=User.ACTIVE,
    )


def get_exporter_contacts(exporter: "Exporter", permission: str | None = None) -> "QuerySet[User]":
    """Return a queryset of users for an exporter with specified permission"""
    if not permission:
        permission = ExporterObjectPermissions.edit.codename

    return User.objects.prefetch_related("exporteruserobjectpermission_set").filter(
        exporteruserobjectpermission__content_object=exporter,
        exporteruserobjectpermission__permission__codename=permission,
        account_status=User.ACTIVE,
    )
