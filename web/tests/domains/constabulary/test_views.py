from django.contrib.auth.models import Permission

from web.domains.constabulary.models import Constabulary
from web.domains.team.models import Role
from web.tests.auth import AuthTestCase

from .factory import ConstabularyFactory

LOGIN_URL = '/'
PERMISSIONS = ['IMP_ADMIN:MAINTAIN_ALL:IMP_MAINTAIN_ALL']


class ConstabularyListViewTest(AuthTestCase):
    url = '/constabulary/'
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
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Maintain Constabularies')

    def test_anonymous_post_access_redirects(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

    def test_forbidden_post_access(self):
        self.login()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_archive_constabulary(self):
        self.login_with_permissions(PERMISSIONS)
        self.constabulary = ConstabularyFactory(is_active=True)
        response = self.client.post(self.url, {
            'action': 'archive',
            'item': self.constabulary.id
        })
        self.assertEqual(response.status_code, 200)
        self.constabulary.refresh_from_db()
        self.assertFalse(self.constabulary.is_active)

    def test_number_of_pages(self):
        # Create 51 product legislation as paging lists 50 items per page
        for i in range(62):
            ConstabularyFactory()

        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        page = response.context_data['page']
        self.assertEqual(page.paginator.num_pages, 2)

    def test_page_results(self):
        for i in range(65):
            ConstabularyFactory(is_active=True)
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url + '?page=2')
        page = response.context_data['page']
        self.assertEqual(len(page.object_list), 15)


class ConstabularyCreateViewTest(AuthTestCase):
    url = '/constabulary/new/'
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
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_firearms_authority_role_created(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(
            self.url, {
                'name': 'Testing',
                'region': Constabulary.EAST_MIDLANDS,
                'email': 'test@example.com'
            })
        constabulary = Constabulary.objects.first()
        role_name = f'Constabulary Contacts:Verified Firearms Authority Editor:{constabulary.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_firearms_authority_permission_created(self):
        self.login_with_permissions(PERMISSIONS)
        self.client.post(
            self.url, {
                'name': 'Testing',
                'region': Constabulary.EAST_MIDLANDS,
                'email': 'test@example.com'
            })
        constabulary = Constabulary.objects.first()
        codename = f'IMP_CONSTABULARY_CONTACTS:FIREARMS_AUTHORITY_EDITOR:{constabulary.id}:IMP_EDIT_FIREARMS_AUTHORITY'  # noqa: C0301
        self.assertTrue(Permission.objects.filter(codename=codename).exists())

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'New Constabulary')


class ConstabularyUpdateViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.constabulary = ConstabularyFactory()  # Create a constabulary
        self.url = f'/constabulary/{self.constabulary.id}/edit/'
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
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         f"Editing {self.constabulary}")


class ConstabularyDetailViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.constabulary = ConstabularyFactory()
        self.url = f'/constabulary/{self.constabulary.id}/'
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
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         f"Viewing {self.constabulary}")
