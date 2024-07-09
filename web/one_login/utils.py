import base64
import json
import logging
from typing import Any

import requests
from authlib.integrations.requests_client import OAuth2Session
from authlib.jose import jwt
from authlib.oauth2.rfc7523 import PrivateKeyJWT
from authlib.oidc.core import IDToken
from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, QueryDict
from django.urls import reverse
from django.utils.module_loading import import_string

from . import types

logger = logging.getLogger(__name__)
TOKEN_SESSION_KEY = "_one_login_token"


def get_client(request: HttpRequest) -> OAuth2Session:
    callback_url = reverse("one_login:callback")
    redirect_uri = request.build_absolute_uri(callback_url)

    session = OAuth2Session(
        client_id=get_client_id(request),
        client_secret=get_secret(request),
        token_endpoint_auth_method="private_key_jwt",
        redirect_uri=redirect_uri,
        scope=get_scope(),
        token=request.session.get(TOKEN_SESSION_KEY, None),
    )

    return session


class OneLoginConfig:
    CACHE_KEY = "one_login_metadata_cache"
    CACHE_EXPIRY = 60 * 60  # seconds

    def __init__(self) -> None:
        self._conf: dict[str, Any] = {}

    def get_public_keys(self) -> list[dict[str, str]]:
        # https://docs.sign-in.service.gov.uk/integrate-with-integration-environment/authenticate-your-user/#validate-your-id-token
        resp = requests.get(self.openid_config["jwks_uri"])
        resp.raise_for_status()
        data = resp.json()

        return data["keys"]

    @property
    def openid_config(self) -> dict[str, Any]:
        # Cached on instance
        if self._conf:
            logger.debug("one login conf: using instance attribute")
            return self._conf

        # Cached in redis store
        cache_config = cache.get(self.CACHE_KEY)
        if cache_config:
            logger.debug("one login conf: using cache value")
            self._conf = json.loads(cache_config)
            return self._conf

        # Retrieve and store value
        config = self._get_configuration()
        cache.set(self.CACHE_KEY, json.dumps(config), timeout=self.CACHE_EXPIRY)
        self._conf = config
        logger.debug("one login conf: using fresh value")

        return self._conf

    def _get_configuration(self) -> dict[str, Any]:
        resp = requests.get(settings.GOV_UK_ONE_LOGIN_OPENID_CONFIG_URL)
        resp.raise_for_status()
        metadata = resp.json()

        return metadata

    @property
    def authorise_url(self) -> str:
        return self.openid_config["authorization_endpoint"]

    @property
    def token_url(self) -> str:
        return self.openid_config["token_endpoint"]

    @property
    def userinfo_url(self) -> str:
        return self.openid_config["userinfo_endpoint"]

    @property
    def end_session_url(self) -> str:
        return self.openid_config["end_session_endpoint"]

    @property
    def issuer(self) -> str:
        return self.openid_config["issuer"]


def get_token(request: HttpRequest, auth_code: str) -> dict:
    client = get_client(request)
    config = OneLoginConfig()

    client.register_client_auth_method(PrivateKeyJWT(token_endpoint=config.token_url))

    # https://docs.sign-in.service.gov.uk/integrate-with-integration-environment/authenticate-your-user/#receive-response-for-make-a-token-request
    token = client.fetch_token(
        url=config.token_url,
        code=auth_code,
        # If you’re requesting a refresh token, you must set this parameter to refresh_token.
        # Otherwise, you need to set the parameter to authorization_code.
        grant_type="authorization_code",
        # https://docs.sign-in.service.gov.uk/integrate-with-integration-environment/authenticate-your-user/#make-a-post-request-to-the-token-endpoint
        # Required value when using private_key_jwt auth.
        client_assertion_type="urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    )

    validate_token(request, token)

    return token


def validate_token(request: HttpRequest, token: dict[str, Any]) -> None:
    config = OneLoginConfig()
    stored_nonce = get_oauth_nonce(request)

    # id_token contents:
    # https://docs.sign-in.service.gov.uk/integrate-with-integration-environment/authenticate-your-user/#understand-your-id-token
    claims = jwt.decode(
        token["id_token"],
        config.get_public_keys(),
        claims_cls=IDToken,
        claims_options={
            "iss": {"essential": True, "value": config.issuer},
            "aud": {"essential": True, "value": get_client_id(request)},
        },
        claims_params={"nonce": stored_nonce},
    )
    claims.validate()


def get_userinfo(client: OAuth2Session) -> types.UserInfo:
    config = OneLoginConfig()
    resp = client.get(config.userinfo_url)
    resp.raise_for_status()

    return resp.json()


def has_valid_token(client: OAuth2Session) -> bool:
    # TODO: ICMSLST-2300 Revisit if supporting OIDC back-channel logout.
    return client.token is not None


def store_oauth_state(request: HttpRequest, state: str) -> None:
    request.session[f"{TOKEN_SESSION_KEY}_oauth_state"] = state


def get_oauth_state(request: HttpRequest) -> str | None:
    return request.session.get(f"{TOKEN_SESSION_KEY}_oauth_state", None)


def delete_oauth_state(request: HttpRequest) -> None:
    request.session.delete(f"{TOKEN_SESSION_KEY}_oauth_state")


def store_oauth_nonce(request: HttpRequest, nonce: str) -> None:
    request.session[f"{TOKEN_SESSION_KEY}_oauth_nonce"] = nonce


def get_oauth_nonce(request: HttpRequest) -> str | None:
    return request.session.get(f"{TOKEN_SESSION_KEY}_oauth_nonce", None)


def delete_oauth_nonce(request: HttpRequest) -> None:
    request.session.delete(f"{TOKEN_SESSION_KEY}_oauth_nonce")


def get_secret(request: HttpRequest) -> bytes:
    # key is stored like this: base64 -i private_key.pem so decode.
    return base64.b64decode(get_client_secret(request))  # /PS-IGNORE


def get_scope():
    return getattr(settings, "GOV_UK_ONE_LOGIN_SCOPE", "openid email")


def get_client_id(request: HttpRequest) -> str:
    """Fetch the client id in one of two ways.

    1. Using a function called get_one_login_client_id defined in the module specified at
       GOV_UK_ONE_LOGIN_GET_CLIENT_CONFIG_PATH setting.
    2. Returning the value found in GOV_UK_ONE_LOGIN_CLIENT_ID setting.
    """

    if path := getattr(settings, "GOV_UK_ONE_LOGIN_GET_CLIENT_CONFIG_PATH", None):
        logger.debug(f"Using {path} to find get_one_login_client_id function.")

        get_one_login_client_id = import_string(f"{path}.get_one_login_client_id")

        return get_one_login_client_id(request)

    logger.debug("Using GOV_UK_ONE_LOGIN_CLIENT_ID to find client secret.")

    # Default if custom function not defined
    return getattr(settings, "GOV_UK_ONE_LOGIN_CLIENT_ID", "")


def get_client_secret(request: HttpRequest) -> str:
    """Fetch the client secret in one of two ways.

    1. Using a function called get_one_login_client_secret defined in the module specified at
       GOV_UK_ONE_LOGIN_GET_CLIENT_CONFIG_PATH setting.
    2. Returning the value found in GOV_UK_ONE_LOGIN_CLIENT_SECRET setting.
    """

    if path := getattr(settings, "GOV_UK_ONE_LOGIN_GET_CLIENT_CONFIG_PATH", None):
        logger.debug(f"Using {path} to find get_one_login_client_secret function.")

        get_one_login_client_secret = import_string(f"{path}.get_one_login_client_secret")

        return get_one_login_client_secret(request)

    logger.debug("Using GOV_UK_ONE_LOGIN_CLIENT_SECRET to find client secret.")

    # Default if custom function not defined
    return getattr(settings, "GOV_UK_ONE_LOGIN_CLIENT_SECRET", "")


def get_one_login_logout_url(
    request: HttpRequest, post_logout_redirect_uri: str | None = None
) -> str:
    """Get logout url for logging a user out of GOV.UK One Login.

    https://docs.sign-in.service.gov.uk/integrate-with-integration-environment/managing-your-users-sessions/#log-your-user-out-of-gov-uk-one-login

    :param request: Django HttpRequest instance
    :param post_logout_redirect_uri: Optional redirect url
    """

    url = OneLoginConfig().end_session_url

    if post_logout_redirect_uri:
        qd = QueryDict(mutable=True)
        qd.update(
            {
                "id_token_hint": request.session[TOKEN_SESSION_KEY]["id_token"],
                "post_logout_redirect_uri": post_logout_redirect_uri,
            }
        )
        url = f"{url}?{qd.urlencode()}"

    return url
