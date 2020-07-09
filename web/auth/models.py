from django.contrib.auth.backends import ModelBackend

from web.models import User


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
