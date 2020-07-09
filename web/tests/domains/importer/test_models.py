from django.contrib.auth.models import Permission
from django.test import TestCase

from web.domains.importer.models import Importer
from web.domains.team.models import Role


class ImporterTest(TestCase):
    def create_importer(
        self, is_active=True, type=Importer.ORGANISATION, name="Very Best Importers Ltd.",
    ):
        return Importer.objects.create(is_active=is_active, type=type, name=name)

    def test_create_importer(self):
        importer = self.create_importer()
        self.assertTrue(isinstance(importer, Importer))
        self.assertEqual(importer.name, "Very Best Importers Ltd.")
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
        role_name = f"Importer Contacts:Approve/Reject Agents and Importers:{importer.id}"
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_agent_approve_reject_role_has_default_permissions(self):
        Permission.objects.create(codename="IMP_AGENT_APPROVER", content_type_id=15)
        Permission.objects.create(codename="IMP_SEARCH_CASES_LHS", content_type_id=15)
        Permission.objects.create(codename="MAILSHOT_RECIPIENT", content_type_id=15)
        Permission.objects.create(codename="MANAGE_IMPORTER_ACCOUNT", content_type_id=15)
        importer = self.create_importer()
        role_name = f"Importer Contacts:Approve/Reject Agents and Importers:{importer.id}"
        permissions = Role.objects.get(name=role_name).permissions.all()
        self.assertEqual(len(permissions), 5)
        codenames = []
        for p in permissions:
            codenames.append(p.codename)
        self.assertTrue("IMP_AGENT_APPROVER" in codenames)
        self.assertTrue("IMP_SEARCH_CASES_LHS" in codenames)
        self.assertTrue("MAILSHOT_RECIPIENT" in codenames)
        self.assertTrue("MANAGE_IMPORTER_ACCOUNT" in codenames)
        self.assertTrue("view_approvalrequestprocess" in codenames)

    def test_application_edit_role_created(self):
        importer = self.create_importer()
        role_name = f"Importer Contacts:Edit Applications:{importer.id}"
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_edit_role_has_default_permissions(self):
        Permission.objects.create(codename="IMP_EDIT_APP", content_type_id=15)
        Permission.objects.create(codename="IMP_SEARCH_CASES_LHS", content_type_id=15)
        Permission.objects.create(codename="MAILSHOT_RECIPIENT", content_type_id=15)
        Permission.objects.create(codename="MANAGE_IMPORTER_ACCOUNT", content_type_id=15)
        importer = self.create_importer()
        role_name = f"Importer Contacts:Edit Applications:{importer.id}"
        permissions = Role.objects.get(name=role_name).permissions.all()
        self.assertEqual(len(permissions), 4)
        codenames = []
        for p in permissions:
            codenames.append(p.codename)
        self.assertTrue("IMP_EDIT_APP" in codenames)
        self.assertTrue("IMP_SEARCH_CASES_LHS" in codenames)
        self.assertTrue("MAILSHOT_RECIPIENT" in codenames)
        self.assertTrue("MANAGE_IMPORTER_ACCOUNT" in codenames)

    def test_application_vary_role_created(self):
        importer = self.create_importer()
        role_name = f"Importer Contacts:Vary Applications/Licences:{importer.id}"
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_vary_role_has_default_permissions(self):
        Permission.objects.create(codename="IMP_VARY_APP", content_type_id=15)
        Permission.objects.create(codename="IMP_SEARCH_CASES_LHS", content_type_id=15)
        Permission.objects.create(codename="MAILSHOT_RECIPIENT", content_type_id=15)
        Permission.objects.create(codename="MANAGE_IMPORTER_ACCOUNT", content_type_id=15)
        importer = self.create_importer()
        role_name = f"Importer Contacts:Vary Applications/Licences:{importer.id}"
        permissions = Role.objects.get(name=role_name).permissions.all()
        self.assertEqual(len(permissions), 4)
        codenames = []
        for p in permissions:
            codenames.append(p.codename)
        self.assertTrue("IMP_VARY_APP" in codenames)
        self.assertTrue("IMP_SEARCH_CASES_LHS" in codenames)
        self.assertTrue("MAILSHOT_RECIPIENT" in codenames)
        self.assertTrue("MANAGE_IMPORTER_ACCOUNT" in codenames)

    def test_application_view_role_created(self):
        importer = self.create_importer()
        role_name = f"Importer Contacts:View Applications/Licences:{importer.id}"
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_view_role_permissions_created(self):
        Permission.objects.create(codename="IMP_VIEW_APP", content_type_id=15)
        Permission.objects.create(codename="IMP_SEARCH_CASES_LHS", content_type_id=15)
        Permission.objects.create(codename="MAILSHOT_RECIPIENT", content_type_id=15)
        importer = self.create_importer()
        role_name = f"Importer Contacts:View Applications/Licences:{importer.id}"
        permissions = Role.objects.get(name=role_name).permissions.all()
        self.assertEqual(len(permissions), 3)
        codenames = []
        for p in permissions:
            codenames.append(p.codename)
        self.assertTrue("IMP_VIEW_APP" in codenames)
        self.assertTrue("IMP_SEARCH_CASES_LHS" in codenames)
        self.assertTrue("MAILSHOT_RECIPIENT" in codenames)
