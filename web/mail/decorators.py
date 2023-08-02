from functools import wraps

from django.conf import settings


def override_recipients(f):
    """Helper decorator to override the email addresses returned by the wrapped function.
    If APP_ENV is dev or local and SEND_ALL_EMAILS_TO is set in django settings all emails will be sent to
    the specified email addresses.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if settings.APP_ENV in ("local", "dev") and settings.SEND_ALL_EMAILS_TO:
            return settings.SEND_ALL_EMAILS_TO
        return f(*args, **kwargs)

    return wrapper
