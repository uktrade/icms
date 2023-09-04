from typing import TYPE_CHECKING, Any, Literal

from django.contrib.auth import get_user_model
from django.http import HttpRequest

from . import types
from .utils import get_client, get_userinfo, has_valid_token

if TYPE_CHECKING:
    from django.contrib.auth.models import User

UserModel = get_user_model()
ONE_LOGIN_UNSET_NAME = "one_login_unset"


class OneLoginBackend:
    def authenticate(self, request: HttpRequest, **credentials: Any) -> "User | None":
        user = None
        client = get_client(request)

        if has_valid_token(client):
            userinfo = get_userinfo(client)

            user = self.get_or_create_user(userinfo)

        if user and self.user_can_authenticate(user):
            return user

        return None

    def get_or_create_user(self, profile: types.UserInfo) -> "User":
        id_key = self.get_profile_id_name()

        user, created = UserModel.objects.get_or_create(
            **{UserModel.USERNAME_FIELD: profile[id_key]},
            defaults=self.user_create_mapping(profile),
        )

        if created:
            user.set_unusable_password()
            user.save()

        return user

    def user_create_mapping(self, userinfo: types.UserInfo) -> types.UserCreateData:
        return {
            "email": userinfo["email"],
            "first_name": ONE_LOGIN_UNSET_NAME,
            "last_name": ONE_LOGIN_UNSET_NAME,
        }

    @staticmethod
    def get_profile_id_name() -> Literal["sub"]:
        return "sub"

    def get_user(self, user_id: int) -> "User | None":
        user_cls = get_user_model()

        try:
            return user_cls.objects.get(pk=user_id)

        except user_cls.DoesNotExist:
            return None

    def user_can_authenticate(self, user: "User") -> bool:
        """Reject users with is_active=False.

        Custom user models that don't have that attribute are allowed.
        """

        is_active = getattr(user, "is_active", None)

        return is_active or is_active is None
