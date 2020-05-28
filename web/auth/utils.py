import random
import string

from django.contrib.auth.models import Permission
from django.db.models import Q


def generate_temp_password(length=8):
    """
    Generates a random alphanumerical password of given length.
    Default length is 8
    """
    return ''.join(random.SystemRandom().choices(string.ascii_letters +
                                                 string.digits,
                                                 k=length))


def _get_user_permissions_query(user):
    """
        Returns the queryset for filtering user permissions.
    """
    return Permission.objects.filter(
        Q(group__in=user.groups.all()) | Q(user=user))


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
    return _get_user_permissions_query(user).filter(
        codename__in=permissions).exists()


def has_team_permission(user, teams, permission):
    """
        Check if user has given permission of given list of teams.

        This only covers non-global Teams (Importers/Exporters
        and their agents, constabularies, etc.)

        Given permission includes the placeholder for id as '{id}'

        A list of permissions will be constructed for each of the given teams
        and user will be tested for these permissions
    """
    if user.is_superuser:
        return True
    if not teams:
        return False

    permissions = []
    for team in teams:
        permissions.append(permission.format(id=team.id))

    return has_any_permission(user, permissions)
