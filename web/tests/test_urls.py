from django.test import Client, TestCase
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.tests.conftest import LOGIN_URL


class TestRedirectBaseDomainView:
    def test_authenticated_redirects_to_workbasket(self, importer_client):
        response = importer_client.get("")
        assertRedirects(response, reverse("workbasket"))

        response = importer_client.get("/")
        assertRedirects(response, reverse("workbasket"))

    def test_non_authenticated_redirects_to_login(self, db, client):
        response = client.get("")
        assertRedirects(response, LOGIN_URL)

        response = client.get("/")
        assertRedirects(response, LOGIN_URL)


class TestLogin(TestCase):
    def test_login_render(self):
        response = Client().get(LOGIN_URL)
        assert response.status_code == 200


class TestRegistration(TestCase):
    def test_registration_render(self):
        response = Client().get(reverse("accounts:register"))
        assert response.status_code == 200


class TestResetPassword(TestCase):
    def test_reset_password(self):
        response = Client().get(reverse("accounts:password_reset"))
        assert response.status_code == 200
