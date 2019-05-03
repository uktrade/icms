from django.test import Client
from django.test import TestCase


class TestLogin(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_renders(self):
        response = self.client.get('/')
        assert response.status_code == 200
