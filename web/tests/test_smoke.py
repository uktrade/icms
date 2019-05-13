from django.test import Client
from django.test import TestCase


class TestLogin(TestCase):
    def test_login_renders(self):
        response = Client().get('/')
        assert response.status_code == 200


class TestRegistration(TestCase):
    def test_registration_render(self):
        response = Client().get('/register/')
        assert response.status_code == 200
