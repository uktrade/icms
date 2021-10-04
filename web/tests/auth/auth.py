from typing import Optional

from django.contrib.auth.models import Permission

# from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from web.models import User
from web.tests.domains.user.factory import UserFactory


class AuthTestCase(TestCase):
    # TODO: this might be able to be removed once all old permissions are gone from the code

    def setUp(self):
        self.user = UserFactory(
            username="test_user",
            password="test",
            password_disposition=User.FULL,
            is_superuser=False,
            account_status=User.ACTIVE,
            is_active=True,
        )

    def grant(self, permission_codename):
        permission = Permission.objects.get(codename=permission_codename)
        self.user.user_permissions.add(permission)

    def login(self):
        if not self.client.login(username="test_user", password="test"):
            raise Exception("Login Failed!")

    def login_with_permissions(self, permissions: Optional[list[str]] = None):
        """
        Log user in and grant defined permissions to user for testing
        """
        self.login()

        # Grant permissions to use
        if permissions:
            for p in permissions:
                self.grant(p)
