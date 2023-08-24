from django.db import transaction

from web.models import Email as UserEmail
from web.models import User


def get_legacy_user_by_username(email_address: str) -> User:
    return User.objects.get(username=email_address, icms_v1_user=True)


def migrate_user(current_user: User, old_icms_user: User) -> None:
    """Migrate a user to a V1 ICMS user.

    :param current_user: The current logged-in user (linked to a gov.uk one login account)
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
