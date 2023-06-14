import pytest
from pytest_django.asserts import assertRedirects

from web.models import Constabulary
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL

from .factory import ConstabularyFactory


class TestConstabularyListView(AuthTestCase):
    url = "/constabulary/"
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
            ConstabularyFactory()

        response = self.ilb_admin_client.get(self.url)
        page = response.context_data["page"]
        assert page.paginator.num_pages == 2

    def test_page_results(self):
        for i in range(65):
            ConstabularyFactory(is_active=True)
        response = self.ilb_admin_client.get(self.url + "?page=2")
        page = response.context_data["page"]
        assert len(page.object_list) == 15


class TestConstabularyCreateView(AuthTestCase):
    url = "/constabulary/new/"
    redirect_url = f"{LOGIN_URL}?next={url}"

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
    def setup(self, _setup):
        self.constabulary = ConstabularyFactory()  # Create a constabulary
        self.url = f"/constabulary/{self.constabulary.id}/edit/"
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
    def setup(self, _setup):
        self.constabulary = ConstabularyFactory()
        self.url = f"/constabulary/{self.constabulary.id}/"
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
