from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from web.domains.importer.models import Importer
from web.domains.section5.models import Section5Authority
from web.domains.user.models import User
from web.tests.auth import AuthTestCase
from web.tests.domains.importer.factory import (
    ImporterFactory,
    IndividualImporterFactory,
)
from web.tests.domains.office.factory import OfficeFactory
from web.tests.domains.user.factory import UserFactory

LOGIN_URL = "/"
PERMISSIONS = ["ilb_admin"]


class ImporterListViewTest(AuthTestCase):
    url = reverse("importer-list")
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_superuser_access(self):
        self.login()
        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_admin_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_external_user_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_constabulary_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data["page_title"], "Maintain Importers")

    def test_anonymous_post_access_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_forbidden_post_access(self):
        self.login()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_number_of_pages(self):
        # Create 58 importer as paging lists 50 items per page
        for i in range(58):
            ImporterFactory()

        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        page = response.context_data["page"]
        self.assertEqual(page.paginator.num_pages, 2)

    def test_page_results(self):
        for i in range(53):
            ImporterFactory(is_active=True)
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url + "?page=2")
        page = response.context_data["page"]

        # We have added one to use as a pytest fixture
        self.assertEqual(len(page.object_list), 3 + 1)


class ImporterEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.importer = IndividualImporterFactory()
        self.url = f"/importer/{self.importer.id}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertTrue(f"Editing {self.importer}", response.content)


class IndividualImporterCreateViewTest(AuthTestCase):
    url = "/importer/individual/create/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_importer_created(self):
        self.login_with_permissions(PERMISSIONS)
        other_user = UserFactory.create(
            account_status=User.ACTIVE, permission_codenames=["importer_access"]
        )
        data = {
            "eori_number": "GBPR",
            "user": other_user.pk,
        }
        response = self.client.post(self.url, data)
        importer = Importer.objects.first()
        self.assertRedirects(response, f"/importer/{importer.pk}/edit/")
        self.assertEqual(importer.user, other_user, msg=importer)


class OrganisationImporterCreateViewTest(AuthTestCase):
    url = "/importer/organisation/create/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @patch("web.domains.importer.forms.api_get_company")
    def test_importer_created(self, api_get_company):
        api_get_company.return_value = {
            "registered_office_address": {
                "address_line_1": "60 rue Wiertz",
                "postcode": "B-1047",
                "locality": "Bruxelles",
            }
        }

        self.login_with_permissions(PERMISSIONS)
        data = {
            "eori_number": "GB",
            "name": "test importer",
            "registered_number": "42",
        }
        response = self.client.post(self.url, data)
        importer = Importer.objects.first()
        self.assertRedirects(response, f"/importer/{importer.pk}/edit/")
        self.assertEqual(importer.name, "test importer", msg=importer)


class IndividualAgentCreateViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.importer = IndividualImporterFactory()
        self.url = f"/importer/{self.importer.pk}/agent/individual/create/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_agent_created(self):
        self.login_with_permissions(PERMISSIONS)
        other_user = UserFactory.create(
            account_status=User.ACTIVE, permission_codenames=["importer_access"]
        )
        data = {
            "main_importer": self.importer.pk,
            "user": other_user.pk,
        }
        response = self.client.post(self.url, data)
        agent = Importer.objects.filter(main_importer__isnull=False).first()
        self.assertRedirects(response, f"/importer/agent/{agent.pk}/edit/")
        self.assertEqual(agent.user, other_user, msg=agent)


class OrganisationAgentCreateViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()

        self.importer = ImporterFactory()
        self.url = f"/importer/{self.importer.pk}/agent/organisation/create/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_agent_created(self):
        self.login_with_permissions(PERMISSIONS)
        data = {
            "main_importer": self.importer.pk,
            "registered_number": "42",
            "name": "test importer",
        }
        response = self.client.post(self.url, data)
        agent = Importer.objects.filter(main_importer__isnull=False).first()
        self.assertRedirects(response, f"/importer/agent/{agent.pk}/edit/")
        self.assertEqual(agent.name, "test importer", msg=agent)


class AgentEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        importer = ImporterFactory()
        self.agent = ImporterFactory(is_active=True, type="ORGANISATION", main_importer=importer)

        self.url = f"/importer/agent/{self.agent.pk}/edit/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.login_with_permissions(PERMISSIONS)
        data = {
            "type": "ORGANISATION",
            "name": self.agent.name,
            "registered_number": "quarante-deux",
            "comments": "Alter agent",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, self.url)
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.comments, "Alter agent")
        self.assertEqual(self.agent.registered_number, "quarante-deux")


class AgentArchiveViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.importer = IndividualImporterFactory()
        self.agent = ImporterFactory(
            main_importer=self.importer, type=Importer.ORGANISATION, is_active=True
        )

        self.url = f"/importer/agent/{self.agent.pk}/archive/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(self.url)
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.is_active, False)
        self.assertRedirects(response, f"/importer/{self.importer.pk}/edit/")


class AgentUnarchiveViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.importer = IndividualImporterFactory()
        self.agent = ImporterFactory(
            main_importer=self.importer, type=Importer.ORGANISATION, is_active=False
        )

        self.url = f"/importer/agent/{self.agent.pk}/unarchive/"
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(self.url)
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.is_active, True)
        self.assertRedirects(response, f"/importer/{self.importer.pk}/edit/")


@pytest.mark.django_db
def test_create_section5_authority():
    ilb_admin = UserFactory.create(
        is_active=True,
        account_status=User.ACTIVE,
        password_disposition=User.FULL,
        permission_codenames=["ilb_admin"],
    )
    office_one, office_two = OfficeFactory.create_batch(2, is_active=True)
    importer = ImporterFactory.create(is_active=True, offices=[office_one, office_two])

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    response = client.get(f"/importer/{importer.pk}/section5/create/")
    assert response.status_code == 200

    data = {
        "linked_offices": office_one.pk,
        "reference": "12",
        "postcode": "ox51dw",  # /PS-IGNORE
        "address": "1 Some road Town County",
        "start_date": "01-Dec-2020",
        "end_date": "02-Dec-2020",
        "clausequantity_set-TOTAL_FORMS": 0,
        "clausequantity_set-INITIAL_FORMS": 0,
    }
    response = client.post(f"/importer/{importer.pk}/section5/create/", data=data)
    assert response.status_code == 302

    section5 = Section5Authority.objects.get()
    assert office_one == section5.linked_offices.first()
    assert response["Location"] == f"/importer/section5/{section5.pk}/edit/"
