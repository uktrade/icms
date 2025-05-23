"""Test the cookies/google analytics views."""

from django.conf import settings
from django.http import SimpleCookie
from django.test import override_settings
from django.urls import reverse

from web.sites import SiteName
from web.views.forms import CookieConsentForm


class TestGtmTags:
    def test_site_names_match(self):
        """Testing that the keys used in the GTM container dict match the actual SiteName choices."""
        assert set(settings.GTM_CONTAINER_IDS.keys()) == set(SiteName.labels)

    @override_settings(
        GTM_CONTAINER_IDS={"Manage import licences and export certificates": "cw_container_id"},
    )
    def test_caseworker_tags_rendered_correctly(self, cw_client):
        response = cw_client.get("", follow=True)
        assert "id=cw_container_id" in response.content.decode("utf-8")

    @override_settings(
        GTM_CONTAINER_IDS={"Apply for an export certificate": "export_container_id"},
    )
    def test_export_tags_rendered_correctly(self, exporter_client):
        response = exporter_client.get("", follow=True)
        assert "id=export_container_id" in response.content.decode("utf-8")

    @override_settings(
        GTM_CONTAINER_IDS={"Apply for an import licence": "import_container_id"},
    )
    def test_import_tags_rendered_correctly(self, importer_client):
        response = importer_client.get("", follow=True)
        assert "id=import_container_id" in response.content.decode("utf-8")


class TestCookieConsentPage:
    def test_cookie_consent_page_renders(self, importer_client):
        """Test that the cookie consent page renders."""
        response = importer_client.get("/cookie-consent/")
        assert response.status_code == 200
        context = response.context[0]
        assert isinstance(context["form"], CookieConsentForm)
        assert not context["form"].initial
        assert "Cookies are files saved on your phone" in response.content.decode("utf-8")

    def test_cookie_consent_initial(self, importer_client):
        """Test that the cookie consent page renders with the correct initial values."""
        importer_client.cookies = SimpleCookie({"accepted_ga_cookies": "true"})
        response = importer_client.get("/cookie-consent/")
        assert response.status_code == 200
        context = response.context[0]
        assert context["form"].initial == {"accept_cookies": True}

    def test_cookie_consent_post_accept(self, importer_client):
        response = importer_client.post("/cookie-consent/", {"accept_cookies": "True"})
        assert response.status_code == 302
        assert response.url == reverse("workbasket")

        assert response.cookies["cookie_preferences_set"].value == "true"
        assert response.cookies["cookie_preferences_set"]["max-age"] == 31536000

        assert response.cookies["accepted_ga_cookies"].value == "true"

    def test_cookie_consent_post_decline(self, importer_client):
        response = importer_client.post("/cookie-consent/", {"accept_cookies": "False"})
        assert response.status_code == 302
        assert response.url == reverse("workbasket")

        assert response.cookies["cookie_preferences_set"].value == "true"
        assert response.cookies["cookie_preferences_set"]["max-age"] == 31536000

        assert response.cookies["accepted_ga_cookies"].value == "false"

    def test_cookie_consent_redirect_for_anonymous_user(self, imp_client):
        """imp_client isn't logged in so should redirect to login-start"""

        response = imp_client.post("/cookie-consent/", {"accept_cookies": "True"})
        assert response.status_code == 302
        assert response.url == reverse("login-start")
