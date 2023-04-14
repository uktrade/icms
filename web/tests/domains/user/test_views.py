import pytest
from pytest_django.asserts import assertRedirects

from web.domains.user import User
from web.tests.auth import AuthTestCase
from web.tests.helpers import get_test_client

from .factory import UserFactory

LOGIN_URL = "/"


class TestCurrentUserDetailsView(AuthTestCase):
    url = "/user/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        test_user = UserFactory(
            username="test_user",
            password="test",
            password_disposition=User.FULL,
            is_superuser=False,
            account_status=User.ACTIVE,
            is_active=True,
        )
        self.test_client = get_test_client(test_user)

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_authorized_access(self):
        response = self.test_client.get(self.url)
        assert response.status_code == 200

    def test_post_action_anonymous_access_redirects(self):
        response = self.anonymous_client.post(self.url, {"action": "edit_address"})
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_post_action_authorized_access(self):
        response = self.test_client.post(self.url, {"action": "edit_address"})
        assert response.status_code == 200


class TestUsersListView(AuthTestCase):
    url = "/user/users/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def setup_user(self, account_status=User.ACTIVE):
        self.test_user = UserFactory(account_status=account_status, password_disposition=User.FULL)

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
        assert response.context_data["page_title"] == "Maintain Web User Accounts"

    def test_post_action_anonymous_access_redirects(self):
        response = self.anonymous_client.post(self.url, {"action": "archive"})
        assert response.status_code == 302

    def test_post_action_forbidden_access(self):
        response = self.importer_client.post(self.url, {"action": "archive"})
        assert response.status_code == 403

    def test_block_user(self):
        self.setup_user()

        response = self.ilb_admin_client.post(
            self.url, {"action": "block", "item": self.test_user.id}
        )
        assert response.status_code == 200
        self.test_user.refresh_from_db()
        assert self.test_user.account_status == User.BLOCKED

    def test_activate_user(self):
        self.setup_user(account_status=User.BLOCKED)
        response = self.ilb_admin_client.post(
            self.url, {"action": "activate", "item": self.test_user.id}
        )
        assert response.status_code == 200
        self.test_user.refresh_from_db()
        assert self.test_user.account_status == User.ACTIVE

    def test_cancel_user(self):
        self.setup_user(account_status=User.ACTIVE)

        response = self.ilb_admin_client.post(
            self.url, {"action": "cancel", "item": self.test_user.id}
        )
        assert response.status_code == 200
        self.test_user.refresh_from_db()
        assert self.test_user.account_status == User.CANCELLED

    def test_reissue_password(self):
        self.setup_user(account_status=User.ACTIVE)

        response = self.ilb_admin_client.post(
            self.url, {"action": "re_issue_password", "item": self.test_user.id}
        )
        assert response.status_code == 200
        self.test_user.refresh_from_db()
        assert self.test_user.password_disposition == User.TEMPORARY


class TestUserDetailsView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.test_user = UserFactory()
        self.url = f"/user/users/{self.test_user.id}/"
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

    def test_post_action_anonymous_access_redirects(self):
        response = self.anonymous_client.post(self.url, {"action": "edit_address"})
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_post_action_forbidden_access(self):
        response = self.importer_client.post(self.url, {"action": "edit_address"})
        assert response.status_code == 403

    def test_post_action_authorized_access(self):
        response = self.ilb_admin_client.post(self.url, {"action": "edit_address"})
        assert response.status_code == 200
