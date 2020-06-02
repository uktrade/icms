from web.domains.importer.models import Importer
from web.tests.auth import AuthTestCase
from web.tests.domains.importer.factory import ImporterFactory

LOGIN_URL = '/'
ADMIN_PERMISSIONS = ['IMP_MAINTAIN_ALL']
SECTION5_AUTHORITY_PERMISSIONS = ['IMP_EDIT_SECTION5_AUTHORITY']
FIREARMS_AUTHORITY_PERMISSIONS = ['IMP_EDIT_FIREARMS_AUTHORITY']


class ImporterListViewTest(AuthTestCase):
    url = '/importer/'
    redirect_url = f'{LOGIN_URL}?next={url}'

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

    def x_test_external_user_access(self):
        self.login_with_permissions(SECTION5_AUTHORITY_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def x_test_constabulary_access(self):
        self.login_with_permissions(FIREARMS_AUTHORITY_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Maintain Importers')

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
        page = response.context_data['page']
        self.assertEqual(page.paginator.num_pages, 2)

    def test_page_results(self):
        for i in range(53):
            ImporterFactory(is_active=True)
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url + '?page=2')
        page = response.context_data['page']
        self.assertEqual(len(page.object_list), 3)


class ImporterEditViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.importer = ImporterFactory()
        self.url = f'/importer/{self.importer.id}/edit/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'

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
        self.assertEqual(response.context_data['page_title'],
                         f"Editing {self.importer}")


class ImporterCreateViewTest(AuthTestCase):
    url = '/importer/new/'
    redirect_url = f'{LOGIN_URL}?next={url}'

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
        self.client.post(self.url, {
            'type': Importer.ORGANISATION,
            'name': 'test importer'
        })
        importer = Importer.objects.first()
        self.assertEqual(importer.name, 'test importer')

    def test_page_title(self):
        self.login_with_permissions(ADMIN_PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Create Importer')
