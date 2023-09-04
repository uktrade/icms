from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy

from web.one_login.backends import ONE_LOGIN_UNSET_NAME


class UserFullyRegisteredMiddleware:
    """Check if the user has fully registered.

    Redirects users to update their details if not.
    """

    redirect_to = reverse_lazy("current-user-details")
    logout = reverse_lazy("logout-user")
    account_recovery = reverse_lazy("account-recovery")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if not hasattr(request, "user"):
            raise ImproperlyConfigured("UserFullyRegisteredMiddleware requires a user to be set.")

        user = request.user

        if (
            user.is_authenticated
            # URLs we allow the user to navigate to without updating their details
            and request.path not in [self.redirect_to, self.logout, self.account_recovery]
            and self.redirect_to != request.path
            and (user.first_name == ONE_LOGIN_UNSET_NAME or user.last_name == ONE_LOGIN_UNSET_NAME)
        ):
            messages.info(request, "Please set your Forename and Surname")

            return redirect(reverse("current-user-details"))

        response = self.get_response(request)

        return response
