from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from functools import wraps


def require_registered(function):
    """
    Ensures user is logged in and has set a password after registration.
    Redirects to set first time password set view if not set.

    A user is marked registered after initial password setup
    """

    @wraps(function)
    def wrap(request, *args, **kwargs):
        decorated_view_func = login_required(request)
        if not decorated_view_func.user.is_authenticated:
            return decorated_view_func(request)  # return redirect to login

        if not request.user.register_complete:
            return redirect('set-password')
        else:
            return function(request, *args, **kwargs)

    return wrap
