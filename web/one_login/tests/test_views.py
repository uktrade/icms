from http import HTTPStatus
from unittest import mock

import pytest
from authlib.jose.errors import InvalidClaimError
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse

from web.one_login.utils import TOKEN_SESSION_KEY, OneLoginConfig
from web.one_login.views import REDIRECT_SESSION_FIELD_NAME

FAKE_OPENID_CONFIG_URL = "https://oidc.onelogin.gov.uk/.well-known/openid-configuration"
FAKE_AUTHORIZE_URL = "https://oidc.onelogin.gov.uk/authorize"


@pytest.fixture(autouse=True, scope="class")
def correct_settings():
    """Ensure One Login is enabled for all tests"""
    with override_settings(
        GOV_UK_ONE_LOGIN_ENABLED=True,
        GOV_UK_ONE_LOGIN_OPENID_CONFIG_URL=FAKE_OPENID_CONFIG_URL,
        # Required to fix tests (these tests don't really care about SITE_ID)
        SITE_ID=1,
    ):
        yield None

    # Teardown the fake openid config at the end of the test session
    # Required otherwise it will use this value when running the real application
    # Also needed if you want to check the mock values in openid_config fixture.
    cache.delete(OneLoginConfig.CACHE_KEY)


@pytest.fixture(autouse=True)
def openid_config(requests_mock):
    requests_mock.get(
        FAKE_OPENID_CONFIG_URL,
        json={
            "authorization_endpoint": FAKE_AUTHORIZE_URL,
            "token_endpoint": "",
            "userinfo_endpoint": "",
            "end_session_endpoint": "",
            "issuer": "",
        },
    )


class TestAuthView:
    @pytest.fixture(autouse=True)
    def setup(self, db, client):
        self.client = client
        self.url = reverse("one_login:login")

    def test_auth_view(self):
        response = self.client.get(self.url)

        assert response.status_code == HTTPStatus.FOUND
        assert FAKE_AUTHORIZE_URL in response.url

    def test_auth_view_retains_next_url(self):
        response = self.client.get(self.url + "?next=/workbasket/")
        assert response.status_code == HTTPStatus.FOUND
        assert self.client.session[REDIRECT_SESSION_FIELD_NAME] == "/workbasket/"

    def test_auth_view_retains_unsafe_next_url(self):
        response = self.client.get(self.url + "?next=https://danger.com")
        assert response.status_code == HTTPStatus.FOUND
        assert not self.client.session[REDIRECT_SESSION_FIELD_NAME]


class TestAuthCallbackView:
    @pytest.fixture(autouse=True)
    def setup(self, db, client):
        self.client = client
        self.url = reverse("one_login:callback")

    @mock.patch.multiple(
        "web.one_login.views",
        get_oauth_state=mock.DEFAULT,
        get_token=mock.DEFAULT,
        authenticate=mock.DEFAULT,
        login=mock.DEFAULT,
        autospec=True,
    )
    def test_auth_callback_view(self, **mocks):
        auth_code = "fake-auth-code"
        state = "fake-state"

        mocks["get_oauth_state"].return_value = state
        mocks["get_token"].return_value = {"token": "fake"}

        response = self.client.get(f"{self.url}?code={auth_code}&state={state}")

        assert self.client.session[TOKEN_SESSION_KEY] == {"token": "fake"}
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(settings.LOGIN_REDIRECT_URL)

    @mock.patch.multiple(
        "web.one_login.views",
        get_oauth_state=mock.DEFAULT,
        get_token=mock.DEFAULT,
        authenticate=mock.DEFAULT,
        login=mock.DEFAULT,
        autospec=True,
    )
    def test_auth_callback_view_with_next_url(self, **mocks):
        next_url = reverse("case:search", kwargs={"case_type": "import", "mode": "standard"})

        # Magic session variable dance to persist session
        # https://docs.djangoproject.com/en/4.2/topics/testing/tools/#django.test.Client.session
        session = self.client.session
        session[REDIRECT_SESSION_FIELD_NAME] = next_url
        session.save()

        auth_code = "fake-auth-code"
        state = "fake-state"
        mocks["get_oauth_state"].return_value = state
        mocks["get_token"].return_value = {"token": "fake"}

        response = self.client.get(f"{self.url}?code={auth_code}&state={state}")

        assert self.client.session[TOKEN_SESSION_KEY] == {"token": "fake"}
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == next_url

    def test_auth_callback_view_no_code(self, caplog):
        response = self.client.get(f"{self.url}")

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("login-start")
        assert caplog.messages[0] == "No auth code returned from one_login"

    def test_auth_callback_view_no_session_state(self, caplog):
        auth_code = "fake-auth-code"
        state = "fake-state"

        response = self.client.get(f"{self.url}?code={auth_code}&state={state}")
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert caplog.messages[0] == "No state found in session"

    @mock.patch.multiple("web.one_login.views", get_oauth_state=mock.DEFAULT, autospec=True)
    def test_auth_callback_view_invalid_state(self, caplog, **mocks):
        auth_code = "fake-auth-code"
        state = "invalid-fake-state"
        mocks["get_oauth_state"].return_value = "fake-state"

        response = self.client.get(f"{self.url}?code={auth_code}&state={state}")
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert caplog.messages[0] == "Session state and passed back state differ"

    @mock.patch.multiple(
        "web.one_login.views", get_oauth_state=mock.DEFAULT, get_token=mock.DEFAULT, autospec=True
    )
    def test_auth_callback_view_invalid_token(self, caplog, **mocks):
        auth_code = "fake-auth-code"
        state = "fake-state"

        mocks["get_oauth_state"].return_value = state
        mocks["get_token"].side_effect = InvalidClaimError("claim_value")

        response = self.client.get(f"{self.url}?code={auth_code}&state={state}")
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert caplog.messages[0] == "Unable to validate token"
