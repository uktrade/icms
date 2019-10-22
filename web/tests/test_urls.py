from django.test import Client
from django.test import TestCase


class TestLogin(TestCase):
    def test_login_render(self):
        response = Client().get('/')
        assert response.status_code == 200


class TestRegistration(TestCase):
    def test_registration_render(self):
        response = Client().get('/register/')
        assert response.status_code == 200


class TestResetPassword(TestCase):
    def test_reset_password(self):
        response = Client().get('/reset-password/')
        assert response.status_code == 200
