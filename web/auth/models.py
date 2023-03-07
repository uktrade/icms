from django.contrib.auth.backends import ModelBackend
from guardian.conf import settings as guardian_settings

from web.models import User


# https://django-guardian.readthedocs.io/en/stable/userguide/custom-user-model.html#anonymous-user-creation
def get_anonymous_user_instance(UserModel: type[User]) -> User:
    # Change the guardian anonymous user pk to match V1 guest user
    kwargs = {
        "pk": 0,
        UserModel.USERNAME_FIELD: guardian_settings.ANONYMOUS_USER_NAME,
    }
    user = UserModel(**kwargs)
    user.set_unusable_password()
    return user


class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None):
        authenticated_user = super().authenticate(request, username, password)

        if authenticated_user is None:
            try:
                unauthenticated_user = User.objects.get_by_natural_key(username)
            except Exception:
                return None

            if (
                unauthenticated_user is not None
                and unauthenticated_user.account_status != User.SUSPENDED
            ):
                unauthenticated_user.unsuccessful_login_attempts += 1
                if unauthenticated_user.unsuccessful_login_attempts > 4:
                    unauthenticated_user.account_status = User.SUSPENDED
                unauthenticated_user.save()
        else:
            authenticated_user.unsuccessful_login_attempts = 0
            authenticated_user.save()
            return authenticated_user
