from web.domains.importer.models import Importer
from web.tests.auth import AuthTestCase
from web.tests.domains.importer.factory import ImporterFactory

LOGIN_URL = '/'
IMPORTER_PERMISSION = 'IMP_IMPORTER_CONTACTS:EDIT_APP:{id}:IMP_EDIT_APP'
AGENT_PERMISSION = 'IMP_IMPORTER_AGENT_CONTACTS:EDIT_APP:{id}:IMP_EDIT_APP'


class ImportAppplicationCreateViewTest(AuthTestCase):
    url = '/import/apply/'
    redirect_url = f'{LOGIN_URL}?next={url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_organisation_importer_access(self):
        importer = ImporterFactory(is_active=True, type=Importer.ORGANISATION)
        importer.members.add(self.user)
        permission = IMPORTER_PERMISSION.format(id=importer.id)
        self.login_with_permissions([permission])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_individual_importer_access(self):
        importer = ImporterFactory(is_active=True,
                                   type=Importer.INDIVIDUAL,
                                   user=self.user)
        permission = IMPORTER_PERMISSION.format(id=importer.id)
        self.login_with_permissions([permission])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_organisation_importer_agent_access(self):
        importer = ImporterFactory(is_active=True)
        agent = ImporterFactory(is_active=True,
                                type=Importer.ORGANISATION,
                                main_importer=importer)
        agent.members.add(self.user)
        permission = AGENT_PERMISSION.format(id=agent.id)
        self.login_with_permissions([permission])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_individual_importer_agent_access(self):
        importer = ImporterFactory(is_active=True)
        agent = ImporterFactory(is_active=True,
                                type=Importer.INDIVIDUAL,
                                main_importer=importer,
                                user=self.user)
        permission = AGENT_PERMISSION.format(id=agent.id)
        self.login_with_permissions([permission])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_post_access_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_forbidden_post_access(self):
        self.login()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
