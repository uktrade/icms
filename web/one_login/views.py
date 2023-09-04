import enum
import logging
from typing import Any

from authlib.common.security import generate_token
from authlib.jose.errors import InvalidClaimError
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login
from django.core.exceptions import SuspiciousOperation
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic.base import RedirectView, View

from .utils import (
    TOKEN_SESSION_KEY,
    OneLoginConfig,
    delete_oauth_nonce,
    delete_oauth_state,
    get_client,
    get_oauth_state,
    get_token,
    store_oauth_nonce,
    store_oauth_state,
)

logger = logging.getLogger(__name__)


# https://docs.sign-in.service.gov.uk/integrate-with-integration-environment/choose-the-level-of-authentication/#choose-the-level-of-authentication-for-your-service
class AuthenticationLevel(enum.StrEnum):
    # Username and Password
    LOW_LEVEL = "Cl"
    # LOW_LEVEL & two-factor authentication
    MEDIUM_LEVEL = "Cl.Cm"


# https://docs.sign-in.service.gov.uk/integrate-with-integration-environment/choose-the-level-of-identity-confidence/
class IdentityConfidenceLevel(enum.StrEnum):
    NONE = "P0"
    LOW = "P1"
    MEDIUM = "P2"


def get_trust_vector(auth_level: str, identity_level: str) -> dict[str, str]:
    return {"vtr": f"['{auth_level}.{identity_level}']"}


REDIRECT_SESSION_FIELD_NAME = f"_oauth2_{REDIRECT_FIELD_NAME}"


def get_next_url(request):
    """Copied straight from staff-sso-client.

    https://github.com/uktrade/django-staff-sso-client/blob/master/authbroker_client/views.py
    """
    next_url = request.GET.get(
        REDIRECT_FIELD_NAME, request.session.get(REDIRECT_SESSION_FIELD_NAME)
    )
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts=settings.ALLOWED_HOSTS, require_https=request.is_secure()
    ):
        return next_url

    return None


class AuthView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        client = get_client(self.request)
        config = OneLoginConfig()

        nonce = generate_token()
        trust_vector = get_trust_vector(
            AuthenticationLevel.MEDIUM_LEVEL, IdentityConfidenceLevel.NONE
        )

        url, state = client.create_authorization_url(
            config.authorise_url,
            nonce=nonce,
            **trust_vector,
        )

        self.request.session[REDIRECT_SESSION_FIELD_NAME] = get_next_url(self.request)
        store_oauth_state(self.request, state)
        store_oauth_nonce(self.request, nonce)

        return url


class AuthCallbackView(View):
    def get(self, request: HttpRequest, *args, **kwargs) -> Any:
        auth_code = self.request.GET.get("code", None)

        if not auth_code:
            logger.error("No auth code returned from one_login")
            return redirect(reverse("login-start"))

        state = get_oauth_state(self.request)
        if not state:
            logger.error("No state found in session")
            raise SuspiciousOperation("No state found in session")

        auth_service_state = self.request.GET.get("state")
        if state != auth_service_state:
            logger.error("Session state and passed back state differ")
            raise SuspiciousOperation("Session state and passed back state differ")

        try:
            token = get_token(self.request, auth_code)
        except InvalidClaimError:
            logger.error("Unable to validate token")
            raise SuspiciousOperation("Unable to validate token")

        self.request.session[TOKEN_SESSION_KEY] = dict(token)
        delete_oauth_state(self.request)
        delete_oauth_nonce(self.request)

        # create the user
        user = authenticate(request)

        if user is not None:
            login(request, user)

        next_url = get_next_url(request) or getattr(settings, "LOGIN_REDIRECT_URL", "/")

        return redirect(next_url)
