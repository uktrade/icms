from django.db.models import QuerySet

from web.auth.backends import ANONYMOUS_USER_PK
from web.models import User


def user_list_view_qs() -> QuerySet[User]:
    """Reusable QuerySet that can be used in several views."""
    return User.objects.exclude(pk=ANONYMOUS_USER_PK).exclude(is_superuser=True)
