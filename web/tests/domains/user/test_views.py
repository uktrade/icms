import pytest
from pytest_django.asserts import assertRedirects

from web.domains.user import User
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL


class TestCurrentUserDetailsView(AuthTestCase):
    url = "/user/"
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_authorized_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 200

    def test_post_action_anonymous_access_redirects(self):
        response = self.anonymous_client.post(self.url, {"action": "edit_address"})
        assert response.status_code == 302
        assertRedirects(response, self.redirect_url)

    def test_post_action_authorized_access(self):
        response = self.importer_client.post(self.url, {"action": "edit_address"})
        assert response.status_code == 200


class TestUsersListView(AuthTestCase):
    url = "/user/users/"
    redirect_url = f"{LOGIN_URL}?next={url}"

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
        response = self.ilb_admin_client.post(
            self.url, {"action": "block", "item": self.importer_user.id}
        )
        assert response.status_code == 200
        self.importer_user.refresh_from_db()
        assert self.importer_user.account_status == User.BLOCKED

    def test_activate_user(self):
        self.importer_two_user.account_status = User.BLOCKED
        self.importer_two_user.save()
        response = self.ilb_admin_client.post(
            self.url, {"action": "activate", "item": self.importer_two_user.id}
        )
        assert response.status_code == 200
        self.importer_two_user.refresh_from_db()
        assert self.importer_two_user.account_status == User.ACTIVE

    def test_cancel_user(self):
        self.importer_two_user.account_status = User.BLOCKED
        self.importer_two_user.save()

        response = self.ilb_admin_client.post(
            self.url, {"action": "cancel", "item": self.importer_two_user.id}
        )
        assert response.status_code == 200
        self.importer_two_user.refresh_from_db()
        assert self.importer_two_user.account_status == User.CANCELLED

    def test_reissue_password(self):
        response = self.ilb_admin_client.post(
            self.url, {"action": "re_issue_password", "item": self.importer_two_user.id}
        )
        assert response.status_code == 200
        self.importer_two_user.refresh_from_db()
        assert self.importer_two_user.password_disposition == User.TEMPORARY


class TestUserDetailsView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = f"/user/users/{self.importer_user.id}/"
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
