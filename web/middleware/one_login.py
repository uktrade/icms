from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import resolve, reverse

from web.models import User
from web.one_login.constants import ONE_LOGIN_UNSET_NAME


class UserFullyRegisteredMiddleware:
    """Check if the user has fully registered.

    Redirects users to update their details if not.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
        if not hasattr(request, "user"):
            raise ImproperlyConfigured("UserFullyRegisteredMiddleware requires a user to be set.")

        user = request.user

        # Views allowed to bypass the UserFullyRegisteredMiddleware
        allowed_views = (
            "new-user-edit",
            "logout-user",
            "account-recovery",
            "contacts:accept-org-invite",
        )

        if (
            user.is_authenticated
            and resolve(request.path).view_name not in allowed_views
            and new_one_login_user(user)
        ):
            messages.info(request, "Please set your first and last name.")  # /PS-IGNORE

            return redirect(reverse("new-user-edit", kwargs={"user_pk": request.user.pk}))

        response = self.get_response(request)

        return response


def new_one_login_user(user: User) -> bool:
    return user.first_name == ONE_LOGIN_UNSET_NAME or user.last_name == ONE_LOGIN_UNSET_NAME
