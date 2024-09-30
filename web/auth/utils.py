import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone

from web.models import Email as UserEmail
from web.models import User
from web.one_login.types import UserCreateData as OneLoginUserCreateData
from web.sites import is_exporter_site, is_importer_site

from .types import StaffSSOUserCreateData

logger = logging.getLogger(__name__)


def get_legacy_user_by_username(email_address: str) -> User:
    return User.objects.get(username__iexact=email_address, icms_v1_user=True)


def migrate_user(current_user: User, old_icms_user: User) -> None:
    """Migrate a user to a V1 ICMS user.

    :param current_user: The current logged-in user (linked to a GOV.UK One Login account)
    :param old_icms_user: A user migrated from ICMS V1.
    """

    new_username = current_user.username
    new_email = current_user.email

    with transaction.atomic():
        # Update the username of the current user.
        current_user = User.objects.select_for_update().get(pk=current_user.pk)
        current_user.username = f"{current_user.username}_v1_migrated"
        current_user.is_active = False
        current_user.email = ""
        current_user.set_unusable_password()
        current_user.save()

        # Update the legacy user with the new username and email
        old_icms_user = User.objects.select_for_update().get(pk=old_icms_user.pk)
        old_icms_user.username = new_username
        old_icms_user.email = new_email
        old_icms_user.save()

        # Make no assumptions on primary email / portal notifications.
        UserEmail.objects.get_or_create(user=old_icms_user, email=new_email)


def get_or_create_icms_user(
    id_value: str, user_data: StaffSSOUserCreateData | OneLoginUserCreateData
) -> tuple[User, bool]:
    provider_email = user_data["email"]
    update_email = False
    created = False

    try:
        # A legacy user is a user who has an email address as a username.
        user = get_legacy_user_by_username(provider_email)

        # Migrate the legacy user to use id_value as username
        user.username = id_value

        user.set_unusable_password()
        user.save()

        update_email = True

    except User.DoesNotExist:
        user, created = User.objects.get_or_create(username=id_value, defaults=user_data)

        if created:
            user.set_unusable_password()
            user.save()
            update_email = True

    if update_email:
        user.email = provider_email
        user.save()

        UserEmail.objects.get_or_create(
            user=user,
            email=provider_email,
            defaults={"is_primary": True, "portal_notifications": True},
        )

    return user, created


def set_site_last_login(user: User, site: Site) -> None:
    if is_importer_site(site):
        user.importer_last_login = timezone.now()
        user.save(update_fields=["importer_last_login"])
    elif is_exporter_site(site):
        user.exporter_last_login = timezone.now()
        user.save(update_fields=["exporter_last_login"])


def get_one_login_client_id(request: HttpRequest) -> str:
    """Used as part of GOV_UK_ONE_LOGIN_GET_CLIENT_CONFIG_PATH to load client id dynamically."""

    if is_exporter_site(request.site):
        logger.debug("Fetching exporter site client id")
        return settings.GOV_UK_ONE_LOGIN_EXPORTER_CLIENT_ID

    if is_importer_site(request.site):
        logger.debug("Fetching importer site client id")
        return settings.GOV_UK_ONE_LOGIN_IMPORTER_CLIENT_ID

    raise ValueError(f"No GOV.UK One Login client ID for site {request.site}")


def get_one_login_client_secret(request: HttpRequest) -> str:
    """Used as part of GOV_UK_ONE_LOGIN_GET_CLIENT_CONFIG_PATH to load client secret dynamically."""

    if is_exporter_site(request.site):
        logger.debug("Fetching exporter site secret")
        return settings.GOV_UK_ONE_LOGIN_EXPORTER_CLIENT_SECRET

    if is_importer_site(request.site):
        logger.debug("Fetching importer site secret")
        return settings.GOV_UK_ONE_LOGIN_IMPORTER_CLIENT_SECRET

    raise ValueError(f"No GOV.UK One Login client secret for site {request.site}")
