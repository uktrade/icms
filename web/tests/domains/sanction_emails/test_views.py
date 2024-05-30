from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects

from web.models import SanctionEmail
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.helpers import get_messages_from_response


class TestSanctionEmailListView(AuthTestCase):

    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("sanction-emails:list")
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_view(self):
        response = self.ilb_admin_client.get(self.url + "?name=")
        assert response.status_code == HTTPStatus.OK
        resp_html = response.content.decode("utf-8")
        assert SanctionEmail.objects.count() == 4
        assert response.context["page_title"] == "Maintain Sanction Emails"
        assertInHTML("Sanction first contact", resp_html, count=1)
        assertInHTML("Sanction deactivated contact", resp_html, count=0)

    def test_view_is_archived_filter(self):
        response = self.ilb_admin_client.get(self.url + "?is_archived=on")
        assert response.status_code == HTTPStatus.OK
        resp_html = response.content.decode("utf-8")
        assertInHTML("Sanction first contact", resp_html, count=0)
        assertInHTML("Sanction deactivated contact", resp_html, count=1)


class TestSanctionEmailCreateView(AuthTestCase):

    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("sanction-emails:create")
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_create_sanction_email_view(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assert response.context["page_title"] == "Create Sanction Email"

        response = self.ilb_admin_client.post(
            self.url,
            data={"name": "test contact", "email": "testcontact@email.com"},  # /PS-IGNORE
        )
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, reverse("sanction-emails:list") + "?name=test+contact")
        assert "New sanction email created successfully." in get_messages_from_response(response)


class TestSanctionEmailEditView(AuthTestCase):

    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.first_contact = SanctionEmail.objects.get(name="Sanction first contact")
        self.url = reverse("sanction-emails:edit", kwargs={"pk": self.first_contact.pk})
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_edit_sanction_email_view(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assert response.context["page_title"] == "Edit Sanction Email"

        response = self.ilb_admin_client.post(
            self.url,
            data={"name": "Sanction Updated Name", "email": self.first_contact.email},
        )
        assert response.status_code == HTTPStatus.FOUND

        assertRedirects(response, reverse("sanction-emails:list") + "?name=Sanction+Updated+Name")
        assert "Sanction email details saved." in get_messages_from_response(response)
