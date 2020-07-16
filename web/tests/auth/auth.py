from django.contrib.auth.models import Permission
from web.models import User

# from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from web.tests.domains.user.factory import UserFactory


class AuthTestCase(TestCase):
    fixtures = ["permission.yaml"]

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
        # TODO: Migrated permissions with django has a fixed content type 15.
        # Create a proxy Permission model for handling permission constants
        # modelless permissions instances.
        # see: https://stackoverflow.com/questions/13932774/how-can-i-use-django-permissions-without-defining-a-content-type-or-model
        permission = Permission.objects.get(codename=permission_codename)
        self.user.user_permissions.add(permission)

    def login(self):
        if not self.client.login(username="test_user", password="test"):
            raise Exception("Login Failed!")

    def login_with_permissions(self, permissions=None):
        """
        Log user in and grant defined permissions to user for testing
        """
        self.login()

        # Grant permissions to use
        if permissions:
            for p in permissions:
                self.grant(p)
