"""Test the cookies/google analytics views."""

import ast

from django.conf import settings
from django.http import SimpleCookie
from django.test import override_settings

from web.sites import SiteName
from web.views.forms import CookieConsentForm


class TestGtmTags:
    def test_site_names_match(self):
        """Testing that the keys used in the GTM dicts match the actual SiteName choices."""
        assert set(settings.GTM_AUTH_KEYS.keys()) == set(SiteName.labels)
        assert set(settings.GTM_CONTAINER_IDS.keys()) == set(SiteName.labels)
        assert set(settings.GTM_PREVIEW_KEYS.keys()) == set(SiteName.labels)

    @override_settings(
        GTM_AUTH_KEYS={"Caseworker": "cw_auth_key"},
        GTM_CONTAINER_IDS={"Caseworker": "cw_container_id"},
        GTM_PREVIEW_KEYS={"Caseworker": "cw_preview_key"},
    )
    def test_caseworker_tags_rendered_correctly(self, cw_client):
        response = cw_client.get("", follow=True)
        assert "gtm_auth=cw_auth_key" in response.content.decode("utf-8")
        assert "gtm_preview=cw_preview_key" in response.content.decode("utf-8")
        assert "id=cw_container_id" in response.content.decode("utf-8")

    @override_settings(
        GTM_AUTH_KEYS={"Export A Certificate": "export_auth_key"},
        GTM_CONTAINER_IDS={"Export A Certificate": "export_container_id"},
        GTM_PREVIEW_KEYS={"Export A Certificate": "export_preview_key"},
    )
    def test_export_tags_rendered_correctly(self, exporter_client):
        response = exporter_client.get("", follow=True)
        assert "gtm_auth=export_auth_key" in response.content.decode("utf-8")
        assert "gtm_preview=export_preview_key" in response.content.decode("utf-8")
        assert "id=export_container_id" in response.content.decode("utf-8")

    @override_settings(
        GTM_AUTH_KEYS={"Import A Licence": "import_auth_key"},
        GTM_CONTAINER_IDS={"Import A Licence": "import_container_id"},
        GTM_PREVIEW_KEYS={"Import A Licence": "import_preview_key"},
    )
    def test_import_tags_rendered_correctly(self, importer_client):
        response = importer_client.get("", follow=True)
        assert "gtm_auth=import_auth_key" in response.content.decode("utf-8")
        assert "gtm_preview=import_preview_key" in response.content.decode("utf-8")
        assert "id=import_container_id" in response.content.decode("utf-8")


class TestCookieConsentPage:
    def test_cookie_consent_page_renders(self, importer_client):
        """Test that the cookie consent page renders."""
        response = importer_client.get("/cookie-consent/")
        assert response.status_code == 200
        context = response.context[0]
        assert isinstance(context["form"], CookieConsentForm)
        assert not context["form"].initial
        assert "Cookies on ICMS" in response.content.decode("utf-8")

    def test_cookie_consent_initial(self, importer_client):
        """Test that the cookie consent page renders with the correct initial values."""
        importer_client.cookies = SimpleCookie({"cookies_policy": {"usage": "true"}})
        response = importer_client.get("/cookie-consent/")
        assert response.status_code == 200
        context = response.context[0]
        assert context["form"].initial == {"accept_cookies": True}

    def test_cookie_consent_post_accept(self, importer_client):
        response = importer_client.post("/cookie-consent/", {"accept_cookies": "True"})
        assert response.status_code == 302
        assert response.url == "/"

        assert response.cookies["cookie_preferences_set"].value == "true"
        assert response.cookies["cookie_preferences_set"]["max-age"] == 31536000

        cookies_policy = ast.literal_eval(response.cookies["cookies_policy"].value)
        assert cookies_policy["essential"] == "true"
        assert cookies_policy["usage"] == "true"

    def test_cookie_consent_post_decline(self, importer_client):
        response = importer_client.post("/cookie-consent/", {"accept_cookies": "False"})
        assert response.status_code == 302
        assert response.url == "/"

        assert response.cookies["cookie_preferences_set"].value == "true"
        assert response.cookies["cookie_preferences_set"]["max-age"] == 31536000

        cookies_policy = ast.literal_eval(response.cookies["cookies_policy"].value)
        assert cookies_policy["essential"] == "true"
        assert cookies_policy["usage"] == "false"

    def test_cookie_consent_redirect_forbidden(self, importer_client):
        """Test that the cookie consent page redirects to the home page if referrer_url supplied is not ours."""
        response = importer_client.post(
            "/cookie-consent/?referrer_url=https://google.com", {"accept_cookies": "True"}
        )
        assert response.status_code == 302
        assert response.url == "/"
