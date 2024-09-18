import pytest
from pytest_django.asserts import assertInHTML, assertRedirects

from web.models import Template
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.views.actions import ArchiveTemplate, Unarchive, UnarchiveTemplate


class TestTemplateListView(AuthTestCase):
    url = "/template/"
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
        assert response.context_data["page_title"] == "Maintain Templates"

    def test_number_of_pages(self):
        response = self.ilb_admin_client.get(self.url, {"template_name_title": ""})
        page = response.context_data["page"]
        assert page.paginator.num_pages == 2

    def test_page_results(self):
        response = self.ilb_admin_client.get(self.url, {"page": "2", "template_name_title": ""})
        page = response.context_data["page"]
        assert len(page.object_list) == 39

    def test_email_template_not_archivable(self):
        response = self.ilb_admin_client.get(self.url, {"template_type": "EMAIL_TEMPLATE"})
        page = response.context_data["page"]
        for _template in page.object_list:
            assert ArchiveTemplate().display(_template) is False
            assert UnarchiveTemplate().display(_template) is False

    def test_archived_not_editable(self):
        """Making sure that the only visible action for archived templates is the unarchive action"""
        new_constabulary = Template.objects.filter(is_active=False).first()
        response = self.ilb_admin_client.get(self.url)
        for action in response.context_data["display"].actions:
            if action.display(new_constabulary) is True:
                assert isinstance(action, Unarchive)


class TestEndorsementCreateView(AuthTestCase):
    url = "/template/endorsement/new/"
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
        assert response.context_data["page_title"] == "New Endorsement"


class TestTemplateEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.template = Template.objects.filter(is_active=True).first()
        self.url = f"/template/{self.template.id}/edit/"
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
        assertInHTML(f"Editing {self.template}", response.content.decode())


class TestTemplateDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.template = Template.objects.filter(is_active=True).first()
        self.url = f"/template/{self.template.id}/"
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
        assertInHTML(f"Viewing {self.template}", response.content.decode())
