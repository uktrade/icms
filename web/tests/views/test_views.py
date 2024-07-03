from http import HTTPStatus
from unittest import mock

import pytest
from django.http import QueryDict
from django.test import override_settings
from django.urls import reverse, reverse_lazy
from pytest_django.asserts import assertRedirects

from web.domains.case.forms_search import ImportSearchForm
from web.domains.contacts.widgets import ContactWidget
from web.one_login.utils import get_one_login_logout_url
from web.tests.auth import AuthTestCase
from web.views import views


class TestRedirectBaseDomainView:
    def test_authenticated_redirects_to_workbasket(self, importer_client):
        response = importer_client.get("")
        assertRedirects(response, reverse("workbasket"))

        response = importer_client.get("/")
        assertRedirects(response, reverse("workbasket"))

    def test_non_authenticated_redirects_to_login(self, db, cw_client):
        response = cw_client.get("")
        assertRedirects(response, reverse("login-start"))

        response = cw_client.get("/")
        assertRedirects(response, reverse("login-start"))


@pytest.mark.parametrize(
    ["staff_sso_enabled", "one_login_enabled", "staff_sso_login_url", "one_login_login_url"],
    [
        (False, False, reverse_lazy("accounts:login"), reverse_lazy("accounts:login")),
        (True, False, reverse_lazy("authbroker_client:login"), reverse_lazy("accounts:login")),
        (False, True, reverse_lazy("accounts:login"), reverse_lazy("one_login:login")),
        (
            True,
            True,
            reverse_lazy("authbroker_client:login"),
            reverse_lazy("one_login:login"),
        ),
    ],
)
def test_login_start_view(
    staff_sso_enabled,
    one_login_enabled,
    staff_sso_login_url,
    one_login_login_url,
    db,
    cw_client,
    exp_client,
    imp_client,
):
    with override_settings(
        STAFF_SSO_ENABLED=staff_sso_enabled, GOV_UK_ONE_LOGIN_ENABLED=one_login_enabled
    ):
        response = cw_client.get(reverse("login-start"))

        assert response.status_code == HTTPStatus.OK
        context = response.context
        assert context["auth_login_url"] == staff_sso_login_url

        response = exp_client.get(reverse("login-start"))
        assert response.status_code == HTTPStatus.OK
        context = response.context
        assert context["auth_login_url"] == one_login_login_url

        response = imp_client.get(reverse("login-start"))
        assert response.status_code == HTTPStatus.OK
        context = response.context
        assert context["auth_login_url"] == one_login_login_url


class TestLogoutView:
    @override_settings(AUTHBROKER_URL="https://fake-sso.trade.gov.uk")
    def test_staff_sso_backend_logout(self, cw_client, ilb_admin_user):
        cw_client.force_login(ilb_admin_user, backend="web.auth.backends.ICMSStaffSSOBackend")

        response = cw_client.post(reverse("logout-user"))

        assertRedirects(
            response, "https://fake-sso.trade.gov.uk/logout/", fetch_redirect_response=False
        )
        self._assert_logged_out(cw_client)

    def test_gov_uk_one_login_backend_logout(self, imp_client, importer_one_contact, monkeypatch):
        imp_client.force_login(
            importer_one_contact, backend="web.auth.backends.ICMSGovUKOneLoginBackend"
        )

        get_one_login_logout_url_mock = mock.create_autospec(spec=get_one_login_logout_url)
        get_one_login_logout_url_mock.return_value = "https://fake-one.login.gov.uk/logout/"
        monkeypatch.setattr(views, "get_one_login_logout_url", get_one_login_logout_url_mock)

        response = imp_client.post(reverse("logout-user"))

        assertRedirects(
            response, "https://fake-one.login.gov.uk/logout/", fetch_redirect_response=False
        )
        self._assert_logged_out(imp_client)

    def test_django_model_auth_backend_logout(self, imp_client, importer_one_contact):
        imp_client.force_login(
            importer_one_contact, backend="web.auth.backends.ModelAndObjectPermissionBackend"
        )

        response = imp_client.post(reverse("logout-user"))

        assertRedirects(response, reverse("login-start"))
        self._assert_logged_out(imp_client)

    def test_unknown_backend_logout(self, db, cw_client, caplog):
        response = cw_client.post(reverse("logout-user"))

        assertRedirects(response, reverse("login-start"))
        self._assert_logged_out(cw_client)

        assert caplog.messages[0] == "Unknown backend: , defaulting to login_start"

    def _assert_logged_out(self, client):
        response = client.get("")
        assertRedirects(response, reverse("login-start"))


class TestSecurityHeaders:
    @override_settings(CSP_REPORT_ONLY=True, CSP_REPORT_URI="https://example.com")
    def test_csp_headers_report_only(self, importer_client):
        response = importer_client.get("")
        assert "Content-Security-Policy-Report-Only" in response.headers
        assert (
            "report-uri https://example.com"
            in response.headers["Content-Security-Policy-Report-Only"]
        )

    @override_settings(CSP_REPORT_ONLY=False)
    def test_normal_csp_headers(self, importer_client):
        response = importer_client.get("")
        assert "Content-Security-Policy" in response.headers

    @override_settings(CSP_REPORT_ONLY=False)
    def test_csp_nonce(self, ilb_admin_client):
        # checking that the script elements have a nonce in them
        with mock.patch("csp.middleware.CSPMiddleware._make_nonce") as mocked_make_nonce:
            mocked_make_nonce.return_value = "test-nonce"
            decoded_response = ilb_admin_client.get(reverse("exporter-create")).content.decode(
                "utf-8"
            )
            assert 'nonce="test-nonce"' in decoded_response

    def test_x_permitted_domains_header(self, importer_client):
        response = importer_client.get("")
        assert "X-Permitted-Cross-Domain-Policies" in response.headers
        assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"


class TestHandler403CaptureProcessErrorView:  # /PS-IGNORE
    @mock.patch("web.views.views.capture_exception")
    def test_default_403_view(self, mock_capture_exception, importer_client):
        # A view that requires the ilb_admin permission
        url = reverse("chief:pending-licences")

        response = importer_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN

        # Only subclasses of ProcessError are sent to sentry
        mock_capture_exception.assert_not_called()

    @mock.patch("web.views.views.capture_exception")
    def test_capture_process_error(
        self, mock_capture_exception, fa_dfl_app_submitted, importer_client
    ):
        # This URL should raise a ProcessError when called as the app is submitted
        url = reverse("import:fa-dfl:edit", kwargs={"application_pk": fa_dfl_app_submitted.pk})

        response = importer_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN

        # capture_exception called as a ProcessError was raised
        mock_capture_exception.assert_called_once()


class TestLoginRequiredSelect2AutoResponseView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        # Query the search page to load the reassignment_user field in to the django_select2 cache.
        response = self.ilb_admin_client.get(
            reverse("case:search", kwargs={"case_type": "import", "mode": "standard"})
        )
        search_form: ImportSearchForm = response.context["form"]
        contact_widget: ContactWidget = search_form.fields["reassignment_user"].widget

        qd = QueryDict(mutable=True)
        qd.update({"term": "ilb_admin_user", "field_id": contact_widget.field_id})
        self.url = reverse("login-required-select2-view") + f"?{qd.urlencode()}"

    def test_can_search_when_authenticated(self):
        response = self.ilb_admin_client.get(self.url)

        assert response.status_code == HTTPStatus.OK
        expected = {
            "more": False,
            "results": [
                {
                    "id": self.ilb_admin_user.id,
                    "text": f"{self.ilb_admin_user.full_name} - {self.ilb_admin_user.email}",
                }
            ],
        }
        assert expected == response.json()

    def test_can_not_search_when_not_authenticated(self):
        response = self.anonymous_client.get(self.url)

        assert response.status_code == HTTPStatus.FORBIDDEN
