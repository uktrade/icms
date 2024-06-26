from typing import TypedDict

from django.http import HttpRequest
from guardian.core import ObjectPermissionChecker

from web.domains.case.types import ImpOrExp

from . import (
    AppChecker,
    can_user_edit_org,
    can_user_manage_org_contacts,
    can_user_view_org,
)
from .service import ORGANISATION


class UserObjectPerms(ObjectPermissionChecker):
    def can_edit_org(self, org: ORGANISATION) -> bool:
        return can_user_edit_org(self.user, org)

    def can_manage_org_contacts(self, org: ORGANISATION) -> bool:
        return can_user_manage_org_contacts(self.user, org)

    def can_user_view_org(self, org: ORGANISATION) -> bool:
        return can_user_view_org(self.user, org)

    def can_view_application(self, application: ImpOrExp) -> bool:
        checker = AppChecker(self.user, application)

        return checker.can_view()

    def can_edit_application(self, application: ImpOrExp) -> bool:
        checker = AppChecker(self.user, application)

        return checker.can_edit()


class UserObjectPermissionsContext(TypedDict):
    user_obj_perms: UserObjectPerms


def request_user_object_permissions(request: HttpRequest) -> UserObjectPermissionsContext:
    """Return context variables required by apps that use the django-guardian permission system.

    If there is no 'user' attribute in the request, use get_anonymous_user (from guardian.utils).
    """

    if hasattr(request, "user"):
        user = request.user
    else:
        from guardian.utils import get_anonymous_user

        user = get_anonymous_user()

    return {"user_obj_perms": UserObjectPerms(user)}
