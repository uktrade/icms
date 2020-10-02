import pytest

from web.domains.importer.models import Importer
from web.domains.office.models import Office
from web.tests.auth import AuthTestCase
from web.tests.domains.importer.factory import ImporterFactory

LOGIN_URL = "/"
ADMIN_PERMISSIONS = ["IMP_MAINTAIN_ALL"]
SECTION5_AUTHORITY_PERMISSIONS = ["IMP_EDIT_SECTION5_AUTHORITY"]
FIREARMS_AUTHORITY_PERMISSIONS = ["IMP_EDIT_FIREARMS_AUTHORITY"]


class ImporterListViewTest(AuthTestCase):
    url = "/importer/"
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
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_external_user_access(self):
        self.login_with_permissions(SECTION5_AUTHORITY_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_constabulary_access(self):
        self.login_with_permissions(FIREARMS_AUTHORITY_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(ADMIN_PERMISSIONS)
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

        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        page = response.context_data["page"]
        self.assertEqual(page.paginator.num_pages, 2)

    def test_page_results(self):
        for i in range(53):
            ImporterFactory(is_active=True)
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url + "?page=2")
        page = response.context_data["page"]
        self.assertEqual(len(page.object_list), 3)


class ImporterEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.importer = ImporterFactory()
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
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(ADMIN_PERMISSIONS)
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
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_importer_created(self):
        self.login_with_permissions(ADMIN_PERMISSIONS)
        data = {
            "eori_number": "GBPR",
            "user": self.user.pk,
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-address": "3 avenue des arbres, Pommier",
            "form-0-postcode": "42000",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, "/importer/")
        importer = Importer.objects.first()
        self.assertEqual(importer.user, self.user, msg=importer)

        office = Office.objects.first()
        self.assertEqual(office.postcode, "42000")


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
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_importer_created(self):
        self.login_with_permissions(ADMIN_PERMISSIONS)
        data = {
            "eori_number": "GB",
            "name": "test importer",
            "form-TOTAL_FORMS": 0,
            "form-INITIAL_FORMS": 0,
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, "/importer/")
        importer = Importer.objects.first()
        self.assertEqual(importer.name, "test importer", msg=importer)


class IndividualAgentCreateViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        base_url = "/importer/{importer_id}/agent/individual/create/"

        self.importer = ImporterFactory()
        self.url = base_url.format(importer_id=self.importer.pk)
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
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_agent_created(self):
        self.login_with_permissions(ADMIN_PERMISSIONS)
        data = {
            "main_importer": self.importer.pk,
            "eori_number": "GBPR",
            "user": self.user.pk,
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-0-address": "3 avenue des arbres, Pommier",
            "form-0-postcode": "42000",
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, "/importer/")
        importer = Importer.objects.filter(main_importer__isnull=False).first()
        self.assertEqual(importer.user, self.user, msg=importer)

        office = Office.objects.first()
        self.assertEqual(office.postcode, "42000")


class OrganisationAgentCreateViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        base_url = "/importer/{importer_id}/agent/organisation/create/"

        self.importer = ImporterFactory()
        self.url = base_url.format(importer_id=self.importer.pk)
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
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_agent_created(self):
        self.login_with_permissions(ADMIN_PERMISSIONS)
        data = {
            "main_importer": self.importer.pk,
            "eori_number": "GB",
            "name": "test importer",
            "form-TOTAL_FORMS": 0,
            "form-INITIAL_FORMS": 0,
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, "/importer/")
        importer = Importer.objects.filter(main_importer__isnull=False).first()
        self.assertEqual(importer.name, "test importer", msg=importer)


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
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @pytest.mark.xfail
    def test_post(self):
        self.login_with_permissions(ADMIN_PERMISSIONS)
        data = {
            "type": "ORGANISATION",
            "action": "edit",
            "name": self.agent.name,
            "registered_number": "quarante-deux",
            "comments": "Alter agent",
            "form-TOTAL_FORMS": 0,
            "form-INITIAL_FORMS": 0,
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, f"/importer/{self.agent.pk}/")
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.comments, "Alter agent")
        self.assertEqual(self.agent.registered_number, "quarante-deux")


class AgentArchiveViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        importer = ImporterFactory()
        self.agent = ImporterFactory(main_importer=importer)

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
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.is_active, False)
        self.assertRedirects(response, f"/importer/agent/{self.agent.pk}/edit/")


class AgentUnarchiveViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        importer = ImporterFactory()
        self.agent = ImporterFactory(main_importer=importer)

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
        self.agent.is_active = False
        self.agent.save()
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.agent.refresh_from_db()
        self.assertEqual(self.agent.is_active, True)
        self.assertRedirects(response, f"/importer/agent/{self.agent.pk}/edit/")
