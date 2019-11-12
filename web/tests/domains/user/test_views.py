from web.tests.auth import AuthTestCase

from .factory import UserFactory

LOGIN_URL = '/'
PERMISSIONS = ['TODO']


class UsersListViewTest(AuthTestCase):
    url = '/users/'
    redirect_url = f'{LOGIN_URL}?next={url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    # def test_forbidden_access(self):
    #     self.login()
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 403)
    #
    # def test_authorized_access(self):
    #     self.login_with_permissions(PERMISSIONS)
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Maintain Web User Accounts')

    # def test_number_of_pages(self):
    #     # Create 51 product legislation as paging lists 50 items per page
    #     for i in range(62):
    #         UserFactory()
    #
    #     self.login_with_permissions(PERMISSIONS)
    #     response = self.client.get(self.url)
    #     page = response.context_data['page']
    #     self.assertEqual(page.paginator.num_pages, 2)

    # def test_page_results(self):
    #     for i in range(65):
    #         UserFactory(is_active=True)
    #     self.login_with_permissions(PERMISSIONS)
    #     response = self.client.get(self.url + '?page=2')
    #     page = response.context_data['page']
    #     self.assertEqual(len(page.object_list), 15)


class UserDetailViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.url = f'/user/{self.user.id}/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'

    # def test_anonymous_access_redirects(self):
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 302)
    #     self.assertRedirects(response, self.redirect_url)

    # def test_forbidden_access(self):
    #     self.login()
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 403)

    # def test_authorized_access(self):
    #     self.login_with_permissions(PERMISSIONS)
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.status_code, 200)

    # def test_page_title(self):
    #     self.login_with_permissions(PERMISSIONS)
    #     response = self.client.get(self.url)
    #     self.assertEqual(response.context_data['page_title'],
    #       "Contact Details")
