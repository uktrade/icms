from django.contrib.auth.models import Permission
from django.test import TestCase

from web.domains.importer.models import Importer
from web.domains.team.models import Role


class ImporterTest(TestCase):
    def create_importer(
        self,
        is_active=True,
        type=Importer.ORGANISATION,
        name='Very Best Importers Ltd.',
    ):
        return Importer.objects.create(is_active=is_active,
                                       type=type,
                                       name=name)

    def test_create_importer(self):
        importer = self.create_importer()
        self.assertTrue(isinstance(importer, Importer))
        self.assertEqual(importer.name, 'Very Best Importers Ltd.')
        self.assertEqual(importer.type, Importer.ORGANISATION)

    def test_archive_importer(self):
        importer = self.create_importer()
        importer.archive()
        self.assertFalse(importer.is_active)

    def test_unarchive_importer(self):
        importer = self.create_importer(is_active=False)
        self.assertFalse(importer.is_active)
        importer.unarchive()
        self.assertTrue(importer.is_active)

    def test_agent_approve_reject_role_created(self):
        importer = self.create_importer()
        role_name = f'Importer Contacts:Approve/Reject Agents and Importers:{importer.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_agent_approve_reject_role_permissions_created(self):
        importer = self.create_importer()
        codename = f'IMP_IMPORTER_CONTACTS:AGENT_APPROVER:{importer.id}:IMP_AGENT_APPROVER'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:AGENT_APPROVER:{importer.id}:IMP_SEARCH_CASES_LHS'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:AGENT_APPROVER:{importer.id}:MAILSHOT_RECIPIENT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:AGENT_APPROVER:{importer.id}:MANAGE_IMPORTER_ACCOUNT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())

    def test_application_edit_role_created(self):
        importer = self.create_importer()
        role_name = f'Importer Contacts:Edit Applications:{importer.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_edit_role_permissions_created(self):
        importer = self.create_importer()
        codename = f'IMP_IMPORTER_CONTACTS:EDIT_APP:{importer.id}:IMP_EDIT_APP'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:EDIT_APP:{importer.id}:IMP_SEARCH_CASES_LHS'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:EDIT_APP:{importer.id}:MAILSHOT_RECIPIENT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:EDIT_APP:{importer.id}:MANAGE_IMPORTER_ACCOUNT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())

    def test_application_vary_role_created(self):
        importer = self.create_importer()
        role_name = f'Importer Contacts:Vary Applications/Licences:{importer.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_vary_role_permissions_created(self):
        importer = self.create_importer()
        codename = f'IMP_IMPORTER_CONTACTS:VARY_APP:{importer.id}:IMP_SEARCH_CASES_LHS'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:VARY_APP:{importer.id}:IMP_VARY_APP'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:VARY_APP:{importer.id}:MAILSHOT_RECIPIENT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:VARY_APP:{importer.id}:MANAGE_IMPORTER_ACCOUNT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())

    def test_application_view_role_created(self):
        importer = self.create_importer()
        role_name = f'Importer Contacts:View Applications/Licences:{importer.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_view_role_permissions_created(self):
        importer = self.create_importer()
        codename = f'IMP_IMPORTER_CONTACTS:VIEW_APP:{importer.id}:IMP_SEARCH_CASES_LHS'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:VIEW_APP:{importer.id}:IMP_VIEW_APP'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_IMPORTER_CONTACTS:VIEW_APP:{importer.id}:MAILSHOT_RECIPIENT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
