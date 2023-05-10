from unittest.mock import patch

import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects

from web.models import Importer, Section5Authority
from web.tests.auth import AuthTestCase
from web.tests.domains.importer.factory import ImporterFactory

LOGIN_URL = "/"


class TestImporterListView(AuthTestCase):
    url = reverse("importer-list")
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_admin_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_external_user_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_constabulary_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == "Maintain Importers"

    def test_anonymous_post_access_redirects(self):
        response = self.anonymous_client.post(self.url)
        assert response.status_code == 302

    def test_forbidden_post_access(self):
        response = self.exporter_client.post(self.url)
        assert response.status_code == 403

    def test_number_of_pages(self):
        # Create 58 importer as paging lists 50 items per page
        for i in range(58):
            ImporterFactory()

        response = self.ilb_admin_client.get(self.url)
        page = response.context_data["page"]
        assert page.paginator.num_pages == 2

    def test_page_results(self):
        for i in range(53):
            ImporterFactory(is_active=True)

        response = self.ilb_admin_client.get(self.url + "?page=2")
        page = response.context_data["page"]

        # We have added two to use as a pytest fixture
        assert len(page.object_list) == 3 + 2


class TestImporterEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer.type = self.importer.INDIVIDUAL
        self.importer.save()

        self.url = f"/importer/{self.importer.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

        resp_html = response.content.decode("utf-8")

        assertInHTML(f"Editing Importer '{self.importer!s}'", resp_html)


class TestIndividualImporterCreateView(AuthTestCase):
    url = "/importer/individual/create/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_importer_created(self):
        data = {
            "eori_number": "GBPR",
            "user": self.importer_user.pk,
        }
        response = self.ilb_admin_client.post(self.url, data)
        importer = Importer.objects.first()
        assertRedirects(response, f"/importer/{importer.pk}/edit/")
        assert importer.user == self.importer_user


class TestOrganisationImporterCreateView(AuthTestCase):
    url = "/importer/organisation/create/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    @patch("web.domains.importer.forms.api_get_company")
    def test_importer_created(self, api_get_company):
        api_get_company.return_value = {
            "registered_office_address": {
                "address_line_1": "60 rue Wiertz",
                "postcode": "B-1047",
                "locality": "Bruxelles",
            }
        }

        data = {
            "eori_number": "GB",
            "name": "test importer",
            "registered_number": "42",
        }
        response = self.ilb_admin_client.post(self.url, data)
        importer = Importer.objects.first()
        assertRedirects(response, f"/importer/{importer.pk}/edit/")
        assert importer.name == "test importer", importer


class TestIndividualAgentCreateView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer.type = self.importer.INDIVIDUAL
        self.importer.save()
        self.url = f"/importer/{self.importer.pk}/agent/individual/create/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_agent_created(self):
        data = {
            "main_importer": self.importer.pk,
            "user": self.importer_user.pk,
        }
        response = self.ilb_admin_client.post(self.url, data)
        agent = Importer.objects.filter(main_importer__isnull=False).first()
        assertRedirects(response, f"/importer/agent/{agent.pk}/edit/")
        assert agent.user == self.importer_user


class TestOrganisationAgentCreateView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer = ImporterFactory()
        self.url = f"/importer/{self.importer.pk}/agent/organisation/create/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_agent_created(self):
        data = {
            "main_importer": self.importer.pk,
            "registered_number": "42",
            "name": "test importer",
        }
        response = self.ilb_admin_client.post(self.url, data)
        agent = Importer.objects.filter(main_importer__isnull=False).first()
        assertRedirects(response, f"/importer/agent/{agent.pk}/edit/")
        assert agent.name == "test importer", agent


class TestAgentEditView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        importer = ImporterFactory()
        self.agent = ImporterFactory(is_active=True, type="ORGANISATION", main_importer=importer)

        self.url = f"/importer/agent/{self.agent.pk}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200

    def test_post(self):
        data = {
            "type": "ORGANISATION",
            "name": self.agent.name,
            "registered_number": "quarante-deux",
            "comments": "Alter agent",
        }
        response = self.ilb_admin_client.post(self.url, data)
        assertRedirects(response, self.url)
        self.agent.refresh_from_db()
        assert self.agent.comments == "Alter agent"
        assert self.agent.registered_number == "quarante-deux"


class TestAgentArchiveView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer.type = self.importer.INDIVIDUAL
        self.importer.save()
        self.agent = ImporterFactory(
            main_importer=self.importer, type=Importer.ORGANISATION, is_active=True
        )

        self.url = f"/importer/agent/{self.agent.pk}/archive/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.post(self.url)
        self.agent.refresh_from_db()
        assert self.agent.is_active is False
        assertRedirects(response, f"/importer/{self.importer.pk}/edit/")


class TestAgentUnarchiveView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.importer.type = self.importer.INDIVIDUAL
        self.importer.save()
        self.agent = ImporterFactory(
            main_importer=self.importer, type=Importer.ORGANISATION, is_active=False
        )

        self.url = f"/importer/agent/{self.agent.pk}/unarchive/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"  #

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.post(self.url)
        self.agent.refresh_from_db()
        assert self.agent.is_active is True
        assertRedirects(response, f"/importer/{self.importer.pk}/edit/")


@pytest.mark.django_db
def test_create_section5_authority(ilb_admin_client, importer, office):
    response = ilb_admin_client.get(f"/importer/{importer.pk}/section5/create/")
    assert response.status_code == 200

    data = {
        "linked_offices": office.pk,
        "reference": "12",
        "postcode": "ox51dw",  # /PS-IGNORE
        "address": "1 Some road Town County",
        "start_date": "01-Dec-2020",
        "end_date": "02-Dec-2020",
        "clausequantity_set-TOTAL_FORMS": 0,
        "clausequantity_set-INITIAL_FORMS": 0,
    }
    response = ilb_admin_client.post(f"/importer/{importer.pk}/section5/create/", data=data)
    assert response.status_code == 302

    section5 = Section5Authority.objects.get()
    assert office == section5.linked_offices.first()
    assert response["Location"] == f"/importer/section5/{section5.pk}/edit/"
