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
