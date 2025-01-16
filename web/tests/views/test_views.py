import logging
from http import HTTPStatus
from unittest import mock

import govuk_onelogin_django
import pytest
from django.conf import settings
from django.http import QueryDict
from django.test import override_settings
from django.urls import reverse, reverse_lazy
from govuk_onelogin_django.utils import get_one_login_logout_url
from pytest_django.asserts import assertRedirects

from web.domains.case.export.forms import CreateExportApplicationForm
from web.domains.case.forms_search import ImportSearchForm
from web.domains.commodity.forms import UsageForm
from web.domains.commodity.widgets import UsageCountryWidget
from web.domains.contacts.widgets import ContactWidget
from web.models import CommodityGroup, ImportApplicationType
from web.tests.auth import AuthTestCase
from web.tests.helpers import get_test_client
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
        assert "<h1>403 Forbidden</h1>" in response.content.decode()

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
        assert "<h1>403 Forbidden</h1>" in response.content.decode()

        # capture_exception called as a ProcessError was raised
        mock_capture_exception.assert_called_once()

    @mock.patch("web.views.views.capture_exception")
    def test_capture_process_error_custom_403_page(
        self, mock_capture_exception, fa_dfl_app_submitted, importer_client
    ):
        # This URL should raise a ProcessError when called as the app is submitted
        url = reverse("import:fa-dfl:submit", kwargs={"application_pk": fa_dfl_app_submitted.pk})

        response = importer_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert "<p>This page is no longer available.</p>" in response.content.decode()

        # capture_exception is not called as we want to ignore this scenario
        mock_capture_exception.assert_not_called()

    @mock.patch("web.views.views.capture_exception")
    def test_capture_process_error_custom_403_page_authorise_documents(
        self, mock_capture_exception, fa_dfl_app_pre_sign, ilb_admin_client
    ):
        # This URL should raise a ProcessError when called as the app is submitted
        url = reverse(
            "case:start-authorisation",
            kwargs={"application_pk": fa_dfl_app_pre_sign.pk, "case_type": "import"},
        )

        response = ilb_admin_client.get(url)

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert "<p>This page is no longer available.</p>" in response.content.decode()

        # capture_exception is not called as we want to ignore this scenario
        mock_capture_exception.assert_not_called()


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

    def test_exporter_search(self, exporter_client, exporter):
        response = exporter_client.get(
            reverse("export:create-application", kwargs={"type_code": "cfs"})
        )
        create_app_form: CreateExportApplicationForm = response.context["form"]
        exporter_widget: ContactWidget = create_app_form.fields["exporter"].widget
        qd = QueryDict(mutable=True)
        qd.update({"term": "Test", "field_id": exporter_widget.field_id})
        url = reverse("login-required-select2-view") + f"?{qd.urlencode()}"

        response = exporter_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            "more": False,
            "results": [
                {
                    "id": 1,
                    "text": "Test Exporter 1",
                },
            ],
        }

    def test_commodity_usage_country(self, ilb_admin_client):
        commodity_group = CommodityGroup.objects.first()
        application_type = ImportApplicationType.objects.get(
            type=ImportApplicationType.Types.WOOD_QUOTA
        )
        url = reverse("commodity-group-usage", kwargs={"pk": commodity_group.pk})
        response = ilb_admin_client.get(url)
        usage_form: UsageForm = response.context["form"]
        country_widget: UsageCountryWidget = usage_form.fields["country"].widget
        qd = QueryDict(mutable=True)
        qd.update({"application_type": application_type.pk, "field_id": country_widget.field_id})
        url = reverse("login-required-select2-view") + f"?{qd.urlencode()}"

        response = ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            "more": False,
            "results": [
                {
                    "id": 122,
                    "text": "Russian Federation",
                },
            ],
        }

    @pytest.mark.parametrize(
        "application_type_str",
        (None, "hello", "hello1"),
    )
    def test_commodity_usage_country_error(self, ilb_admin_client, application_type_str):
        commodity_group = CommodityGroup.objects.first()
        url = reverse("commodity-group-usage", kwargs={"pk": commodity_group.pk})

        response = ilb_admin_client.get(url)
        usage_form: UsageForm = response.context["form"]
        country_widget: UsageCountryWidget = usage_form.fields["country"].widget
        qd = QueryDict(mutable=True)
        qd.update({"application_type": application_type_str, "field_id": country_widget.field_id})
        url = reverse("login-required-select2-view") + f"?{qd.urlencode()}"

        response = ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            "more": False,
            "results": [],
        }


@override_settings(
    APP_ENV="local",
)
def test_banner_colour_change(ilb_admin_client, exporter_client, importer_client):
    response = ilb_admin_client.get(reverse("workbasket"))
    assert "#menu-bar { background: red !important; }" in response.content.decode()

    response = exporter_client.get(reverse("workbasket"))
    assert "#menu-bar { background: grey !important; }" in response.content.decode()

    response = importer_client.get(reverse("workbasket"))
    assert "#menu-bar { background: green !important; }" in response.content.decode()


@override_settings(
    APP_ENV="production",
)
def test_banner_colour_doesnt_change(ilb_admin_client):
    response = ilb_admin_client.get(reverse("workbasket"))
    assert "#menu-bar { background:" not in response.content.decode()


class TestICMSOIDCBackChannelLogoutView:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client):
        self.client = importer_client
        self.url = reverse("one-login-back-channel-logout")

    @mock.patch.object(
        govuk_onelogin_django.views.OIDCBackChannelLogoutView, "validate_logout_token"
    )
    def test_back_channel_logout(
        self, mock_validate_logout_token, importer_site, importer_one_contact
    ):
        response = self.client.get(reverse("workbasket"))
        assert response.status_code == HTTPStatus.OK

        mock_validate_logout_token.return_value = importer_one_contact.username
        # mock_back_channel_logout.validate_logout_token.return_value = importer_one_contact.username

        # Fresh test client to mimic request coming from GOV.UK One Login
        client = get_test_client(importer_site.domain)

        response = client.post(self.url)
        assert response.status_code == HTTPStatus.OK

        login_url = reverse(settings.LOGIN_URL)
        workbasket_url = reverse("workbasket")
        response = self.client.get(workbasket_url, follow=True)
        assertRedirects(response, f"{login_url}?next={workbasket_url}", status_code=302)

    @mock.patch.object(
        govuk_onelogin_django.views.OIDCBackChannelLogoutView, "validate_logout_token"
    )
    def test_back_channel_logout_unknown_sub(
        self, mock_validate_logout_token, importer_site, caplog
    ):
        mock_validate_logout_token.return_value = "unknown"

        response = self.client.post(self.url)
        # Response is always 200 even if there is an error
        assert response.status_code == HTTPStatus.OK

        assert caplog.record_tuples == [
            (
                "web.views.views",
                logging.ERROR,
                "ICMSOIDCBackChannelLogoutView: Unable to log user out with sub: unknown",
            )
        ]
