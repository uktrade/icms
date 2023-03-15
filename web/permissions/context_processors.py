from typing import TypedDict

from django.http import HttpRequest
from guardian.core import ObjectPermissionChecker


class UserObjectPermissionsContext(TypedDict):
    user_obj_perms: ObjectPermissionChecker


def request_user_object_permissions(request: HttpRequest) -> UserObjectPermissionsContext:
    """Return context variables required by apps that use the django-guardian permission system.

    If there is no 'user' attribute in the request, use get_anonymous_user (from guardian.utils).
    """

    if hasattr(request, "user"):
        user = request.user
    else:
        from guardian.utils import get_anonymous_user

        user = get_anonymous_user()

    return {"user_obj_perms": ObjectPermissionChecker(user)}
