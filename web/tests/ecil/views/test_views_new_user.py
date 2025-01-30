from http import HTTPStatus

import pytest
from django.urls import reverse


class TestExporterLoginStartView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client):
        self.url = reverse("ecil:new_user:exporter_login_start")
        self.client = prototype_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post_forbidden(self):
        response = self.client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert response.context["auth_login_url"] == reverse("workbasket")
