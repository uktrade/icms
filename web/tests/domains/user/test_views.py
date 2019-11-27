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

    def test_page_title(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.context_data['page_title'],
                         'Maintain Web User Accounts')


class UserDetailViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.url = f'/user/{self.user.id}/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'
