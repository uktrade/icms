from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from web.ecil.gds import forms as gds_forms


class TestExporterLoginStartView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client):
        self.url = reverse("ecil:new_user:exporter_login_start")
        self.client = prototype_export_client

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

        assert response.context["auth_login_url"] == reverse("ecil:new_user:update_name")


class TestNewUserUpdateNameView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:new_user:update_name")
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        # Check the form instance pk is that of the prototype user
        assert response.context["form"].instance.pk == self.user.pk

    def test_post(self):
        assert self.user.first_name == "prototype_export_user_first_name"
        assert self.user.last_name == "prototype_export_user_last_name"

        form_data = {"first_name": "John", "last_name": "Doe"}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:new_user:exporter_triage")

        self.user.refresh_from_db()
        assert self.user.first_name == "John"
        assert self.user.last_name == "Doe"


class TestNewUserExporterTriageFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:new_user:exporter_triage")
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post(self):
        form_data = {"applications": ["cfs", "gmp", "com"]}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("workbasket")

        form_data = {"applications": [gds_forms.GovUKCheckboxesField.NONE_OF_THESE]}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:new_user:something_else")


class TestNewUserExporterTriageSomethingElseView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:new_user:something_else")
        self.client = prototype_export_client

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
        assertTemplateUsed(response, "ecil/new_user/exporter_triage_something_else.html")
