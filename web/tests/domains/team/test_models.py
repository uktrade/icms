from django.test import TestCase
from web.domains.team.models import Role

from .factory import TeamFactory

class RoleTest(TestCase):
    def create_role(self,
                    name='Test Team:Test Role',
                    description='This is a test role',
                    role_order=1):
        return Role.objects.create(name=name,
                                   description=description,
                                   role_order=role_order,
                                   team=TeamFactory())

    def test_create_role(self):
        role = self.create_role()
        self.assertTrue(isinstance(role, Role))
        self.assertEqual(role.name, 'Test Team:Test Role')
        self.assertEqual(role.description, 'This is a test role')
        self.assertEqual(role.role_order, 1)
