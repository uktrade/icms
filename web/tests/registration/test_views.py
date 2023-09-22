from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects


class TestLegacyAccountRecoveryView:
    @pytest.fixture(autouse=True)
    def _setup(self, one_login_user, legacy_user, imp_client, exp_client):
        self.one_login_client = imp_client
        self.one_login_user = one_login_user
        self.one_login_client.force_login(
            one_login_user, backend="web.auth.backends.ModelAndObjectPermissionBackend"
        )

        self.legacy_user_client = exp_client
        self.legacy_user = legacy_user
        self.legacy_user_client.force_login(
            legacy_user, backend="web.auth.backends.ModelAndObjectPermissionBackend"
        )

        self.url = reverse("account-recovery")

    def test_can_access_view(self):
        response = self.one_login_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.legacy_user_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_migrate_user_success(self):
        data = {"legacy_email": self.legacy_user.email, "legacy_password": "TestPassword1!"}

        response = self.one_login_client.post(self.url, data=data)
        assertRedirects(response, reverse("login-start"), HTTPStatus.FOUND)

        self.one_login_user.refresh_from_db()
        self.legacy_user.refresh_from_db()

        # one_login_user is now inactive
        assert self.one_login_user.username == "one_login_id_v1_migrated"
        assert not self.one_login_user.is_active
        assert self.one_login_user.email == ""
        assert not self.one_login_user.has_usable_password()

        # Test legacy_user has been updated
        assert self.legacy_user.username == "one_login_id"
        assert self.legacy_user.email == "one_login_user@example.com"  # /PS-IGNORE
        assert self.legacy_user.emails.filter(
            email="one_login_user@example.com"  # /PS-IGNORE
        ).exists()
