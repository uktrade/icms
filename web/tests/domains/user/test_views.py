from web.tests.auth import AuthTestCase

from web.domains.user import User

from .factory import UserFactory

LOGIN_URL = '/'
PERMISSIONS = ['DIRECTORY_DTI_SUPER_USERS:WUA_ADMIN:WEB_USER_ACCOUNT_LHS']


class CurrentUserDetailsViewTest(AuthTestCase):
    url = '/user/'
    redirect_url = f'{LOGIN_URL}?next={url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_authorized_access(self):
        self.login()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_action_anonymous_access_redirects(self):
        response = self.client.post(self.url, {'action': 'edit_address'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_post_action_authorized_access(self):
        self.login()
        response = self.client.post(self.url, {'action': 'edit_address'})
        self.assertEqual(response.status_code, 200)


class UsersListViewTest(AuthTestCase):
    url = '/user/users/'
    redirect_url = f'{LOGIN_URL}?next={url}'

    def setup_user(self, account_status=User.ACTIVE):
        self.test_user = UserFactory(account_status=account_status,
                                     password_disposition=User.FULL)

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
                         'Maintain Web User Accounts')

    def test_default_account_status(self):
        user = UserFactory()
        self.assertEqual(user.account_status, User.ACTIVE)

    def test_post_action_anonymous_access_redirects(self):
        response = self.client.post(self.url, {'action': 'archive'})
        self.assertEqual(response.status_code, 302)

    def test_post_action_forbidden_access(self):
        self.login()
        response = self.client.post(self.url, {'action': 'archive'})
        self.assertEqual(response.status_code, 403)

    def test_block_user(self):
        self.setup_user()
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(self.url, {
            'action': 'block',
            'item': self.test_user.id
        })
        self.assertEqual(response.status_code, 200)
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.account_status, User.BLOCKED)

    def test_activate_user(self):
        self.setup_user(account_status=User.BLOCKED)
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(self.url, {
            'action': 'activate',
            'item': self.test_user.id
        })
        self.assertEqual(response.status_code, 200)
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.account_status, User.ACTIVE)

    def test_cancel_user(self):
        self.setup_user(account_status=User.ACTIVE)
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(self.url, {
            'action': 'cancel',
            'item': self.test_user.id
        })
        self.assertEqual(response.status_code, 200)
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.account_status, User.CANCELLED)

    def test_reissue_password(self):
        self.setup_user(account_status=User.ACTIVE)
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(self.url, {
            'action': 're_issue_password',
            'item': self.test_user.id
        })
        self.assertEqual(response.status_code, 200)
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.password_disposition, User.TEMPORARY)


class UserDetailsViewTest(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.test_user = UserFactory()
        self.url = f'/user/users/{self.test_user.id}/'
        self.redirect_url = f'{LOGIN_URL}?next={self.url}'

    def test_anonymous_access_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        self.login()
        response = self.client.get(self.url)
        print(response)
        self.assertEqual(response.status_code, 403)

    def test_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_action_anonymous_access_redirects(self):
        response = self.client.post(self.url, {'action': 'edit_address'})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.redirect_url)

    def test_post_action_forbidden_access(self):
        self.login()
        response = self.client.post(self.url, {'action': 'edit_address'})
        self.assertEqual(response.status_code, 403)

    def test_post_action_authorized_access(self):
        self.login_with_permissions(PERMISSIONS)
        response = self.client.post(self.url, {'action': 'edit_address'})
        self.assertEqual(response.status_code, 200)
