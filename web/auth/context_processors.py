from typing import Any

from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse


def auth(request: HttpRequest) -> dict[str, Any]:
    """Return context variables relating to authentication."""

    return {
        "login_url": reverse(settings.LOGIN_URL),
        "logout_url": reverse("logout-user"),
    }
