from http import HTTPStatus

import pytest
from django.test import override_settings
from django.urls import reverse, reverse_lazy
from pytest_django.asserts import assertRedirects


class TestRedirectBaseDomainView:
    def test_authenticated_redirects_to_workbasket(self, importer_client):
        response = importer_client.get("")
        assertRedirects(response, reverse("workbasket"))

        response = importer_client.get("/")
        assertRedirects(response, reverse("workbasket"))

    def test_non_authenticated_redirects_to_login(self, db, client):
        response = client.get("")
        assertRedirects(response, reverse("login-start"))

        response = client.get("/")
        assertRedirects(response, reverse("login-start"))


@pytest.mark.parametrize(
    ["staff_sso_enabled", "one_login_enabled", "staff_sso_login_url", "one_login_login_url"],
    [
        (False, False, reverse_lazy("accounts:login"), reverse_lazy("accounts:login")),
        (True, False, reverse_lazy("authbroker_client:login"), reverse_lazy("accounts:login")),
        # TODO: ICMSLST-2196 Replace with gov.uk one login url
        (False, True, reverse_lazy("accounts:login"), reverse_lazy("authbroker_client:login")),
        (
            True,
            True,
            reverse_lazy("authbroker_client:login"),
            reverse_lazy("authbroker_client:login"),
        ),
    ],
)
def test_login_start_view(
    staff_sso_enabled, one_login_enabled, staff_sso_login_url, one_login_login_url, db, client
):
    with override_settings(
        STAFF_SSO_ENABLED=staff_sso_enabled, GOV_UK_ONE_LOGIN_ENABLED=one_login_enabled
    ):
        response = client.get(reverse("login-start"))

        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["staff_sso_login_url"] == staff_sso_login_url
        assert context["one_login_login_url"] == one_login_login_url


class TestLogoutView:
    @override_settings(AUTHBROKER_URL="https://fake-sso.trade.gov.uk")
    def test_staff_sso_backend_logout(self, client, ilb_admin_user):
        client.force_login(ilb_admin_user, backend="web.auth.backends.ICMSStaffSSOBackend")

        response = client.post(reverse("logout-user"))

        assertRedirects(
            response, "https://fake-sso.trade.gov.uk/logout/", fetch_redirect_response=False
        )
        self._assert_logged_out(client)

    def test_gov_uk_one_login_backend_logout(self, client, importer_one_contact):
        client.force_login(importer_one_contact, backend="web.auth.backends.GovUKOneLoginBackend")

        response = client.post(reverse("logout-user"))

        # TODO: ICMSLST-2196 Replace with gov.uk one login url
        assertRedirects(response, reverse("login-start"), fetch_redirect_response=False)
        self._assert_logged_out(client)

    def test_django_model_auth_backend_logout(self, client, importer_one_contact):
        client.force_login(
            importer_one_contact, backend="web.auth.backends.ModelAndObjectPermissionBackend"
        )

        response = client.post(reverse("logout-user"))

        assertRedirects(response, reverse("login-start"))
        self._assert_logged_out(client)

    def test_unknown_backend_logout(self, db, client, caplog):
        response = client.post(reverse("logout-user"))

        assertRedirects(response, reverse("login-start"))
        self._assert_logged_out(client)

        assert caplog.messages[0] == "Unknown backend: , defaulting to login_start"

    def _assert_logged_out(self, client):
        response = client.get("")
        assertRedirects(response, reverse("login-start"))
