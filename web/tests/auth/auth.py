from django.contrib.auth.models import Permission
from web.models import User
# from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from web.tests.domains.user.factory import UserFactory


class AuthTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(username='test_user',
                                password='test',
                                password_disposition=User.FULL,
                                is_superuser=False,
                                is_active=True)

    def grant(self, permission_codename):
        permission = Permission.objects.create(name=permission_codename,
                                               codename=permission_codename,
                                               content_type_id=15)
        self.user.user_permissions.add(permission)

    def login(self):
        if not self.client.login(username='test_user', password='test'):
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
