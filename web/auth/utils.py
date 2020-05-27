import random
import string

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from web.domains.team.models import Role


def generate_temp_password(length=8):
    """
    Generates a random alphanumerical password of given length.
    Default length is 8
    """
    return ''.join(random.SystemRandom().choices(string.ascii_letters +
                                                 string.digits,
                                                 k=length))


def create_team_roles(team, roles):
    """
        Creates given roles and permissions for given team
    """
    for r in roles:
        role = Role.objects.create(name=r['name'].format(id=team.id),
                                   description=r['description'],
                                   role_order=r['role_order'])

        permissions = []
        for p in r['permissions']:
            permission = Permission.objects.create(
                codename=p['codename'].format(id=team.id),
                name=p['name'],
                content_type=ContentType.objects.get_for_model(team))
            permissions.append(permission)

        role.permissions.add(*permissions)
