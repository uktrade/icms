from django.test import Client, TestCase
from django.urls import reverse

from web.tests.conftest import LOGIN_URL


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
