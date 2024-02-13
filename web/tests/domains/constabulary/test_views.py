from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.models import Constabulary
from web.permissions import constabulary_get_contacts
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.helpers import get_test_client

from .factory import ConstabularyFactory


class TestConstabularyListView(AuthTestCase):
    url = reverse("constabulary:list")
    redirect_url = f"{LOGIN_URL}?next={url}"

    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        # These tests pre-date the data migration that adds constabularies
        # therefore delete all real constabulary records before running these tests
        Constabulary.objects.all().delete()

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == "Maintain Constabularies"

    def test_anonymous_post_access_redirects(self):
        response = self.anonymous_client.post(self.url)
        assert response.status_code == 302

    def test_forbidden_post_access(self):
        response = self.importer_client.post(self.url)
        assert response.status_code == 403

    def test_archive_constabulary(self):
        self.constabulary = ConstabularyFactory(is_active=True)
        response = self.ilb_admin_client.post(
            self.url, {"action": "archive", "item": self.constabulary.id}
        )
        assert response.status_code == 200
        self.constabulary.refresh_from_db()
        assert self.constabulary.is_active is False

    def test_number_of_pages(self):
        # Create 51 product legislation as paging lists 50 items per page
        for i in range(62):
            ConstabularyFactory(is_active=True)

        response = self.ilb_admin_client.get(self.url, {"name": ""})
        page = response.context_data["page"]
        assert page.paginator.num_pages == 2

    def test_page_results(self):
        for i in range(65):
            ConstabularyFactory(is_active=True)
        response = self.ilb_admin_client.get(self.url, {"page": "2", "name": ""})
        page = response.context_data["page"]
        assert len(page.object_list) == 15


class TestConstabularyCreateView(AuthTestCase):
    url = reverse("constabulary:new")
    redirect_url = f"{LOGIN_URL}?next={url}"

    @pytest.fixture(autouse=True)
    def setup(self, _setup, strict_templates): ...

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == "New Constabulary"


class TestConstabularyUpdateView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, strict_templates):
        self.constabulary = ConstabularyFactory()  # Create a constabulary
        self.url = reverse("constabulary:edit", kwargs={"pk": self.constabulary.id})
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == f"Editing {self.constabulary}"


class TestConstabularyDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, strict_templates):
        self.constabulary = ConstabularyFactory()
        self.url = reverse("constabulary:detail", kwargs={"pk": self.constabulary.id})
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == f"Viewing {self.constabulary}"


class TestAddConstabularyContactView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, constabulary_contact, strict_templates, caseworker_site):
        self.con_user = constabulary_contact
        self.con_client = get_test_client(caseworker_site.domain, self.con_user)
        self.constabulary = Constabulary.objects.get(name="Cumbria")
        self.url = reverse("constabulary:add-contact", kwargs={"pk": self.constabulary.pk})

    def test_get_forbidden(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_permission(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.con_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_add_constabulary_contact(self):
        assert constabulary_get_contacts(self.constabulary).count() == 0

        form_data = {"contact": self.con_user.pk}
        response = self.ilb_admin_client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        contacts = constabulary_get_contacts(self.constabulary)
        assert contacts.count() == 1

        assert contacts[0] == self.con_user


class TestDeleteConstabularyContactView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, constabulary_contact, strict_templates, caseworker_site):
        self.con_user = constabulary_contact
        self.con_client = get_test_client(caseworker_site.domain, self.con_user)
        # A constabulary the user is already linked to
        self.constabulary = Constabulary.objects.get(name="Derbyshire")
        self.url = reverse(
            "constabulary:delete-contact",
            kwargs={"pk": self.constabulary.pk, "contact_pk": self.con_user.pk},
        )

    def test_get_forbidden(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_permission(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.importer_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.con_client.post(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_add_constabulary_contact(self):
        contacts = constabulary_get_contacts(self.constabulary)
        assert contacts.count() == 1
        assert contacts[0] == self.con_user

        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        contacts = constabulary_get_contacts(self.constabulary)
        assert contacts.count() == 0
