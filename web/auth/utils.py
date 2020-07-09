import random
import string

import structlog as logging
from django.contrib.auth.models import Permission
from django.db.models import Q

from web.domains.user.models import User

logger = logging.getLogger(__name__)


def generate_temp_password(length=8):
    """
    Generates a random alphanumerical password of given length.
    Default length is 8
    """
    return "".join(random.SystemRandom().choices(string.ascii_letters + string.digits, k=length))


def get_users_with_permission(permission_name):
    """
        Return all users who has given permission

        permission is in app_label.codename format
    """
    if permission_name:
        app_label, codename = permission_name.split(".")
        permission = Permission.objects.get(codename=codename)
        users = User.objects.filter(
            Q(groups__permissions=permission) | Q(user_permissions=permission)
        )
    else:
        users = User.objects.none()
    return users


def get_team_members_with_permission(team, permission_name):
    """
        Return all members of given team who has given permission
    """
    if permission_name:
        app_label, codename = permission_name.split(".")
        permission = Permission.objects.get(codename=codename)
        users = team.members.filter(
            Q(groups__permissions=permission) | Q(user_permissions=permission)
        )
    else:
        users = team.members

    return users


def _get_user_permissions_query(user):
    """
        Returns the queryset for filtering user permissions.
    """
    return Permission.objects.filter(Q(group__in=user.groups.all()) | Q(user=user))


def get_user_permissions(user):
    """
        Returns a list of all permissions user was granted either
        directly or via a group the user is in.
    """
    return _get_user_permissions_query(user).all()


def has_any_permission(user, permissions=[]):
    """
        Checks if user has any of the given permissions
    """
    if user.is_superuser:
        return True
    return _get_user_permissions_query(user).filter(codename__in=permissions).exists()
