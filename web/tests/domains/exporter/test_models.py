from django.contrib.auth.models import Permission
from django.test import TestCase

from web.domains.exporter.models import Exporter
from web.domains.team.models import Role


class ExporterTest(TestCase):
    def create_exporter(self, is_active=True, name="The Exporters Ltd."):
        return Exporter.objects.create(is_active=is_active, name=name)

    def test_create_exporter(self):
        exporter = self.create_exporter()
        self.assertTrue(isinstance(exporter, Exporter))
        self.assertEqual(exporter.name, "The Exporters Ltd.")

    def test_archive_exporter(self):
        exporter = self.create_exporter()
        exporter.archive()
        self.assertFalse(exporter.is_active)

    def test_unarchive_exporter(self):
        exporter = self.create_exporter(is_active=False)
        self.assertFalse(exporter.is_active)
        exporter.unarchive()
        self.assertTrue(exporter.is_active)

    def test_agent_approve_reject_role_created(self):
        exporter = self.create_exporter()
        role_name = f"Exporter Contacts:Approve/Reject Agents and Exporters:{exporter.id}"
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_agent_approve_reject_role_has_default_permissions(self):
        Permission.objects.create(codename="IMP_CERT_AGENT_APPROVER", content_type_id=15)
        Permission.objects.create(codename="IMP_CERT_SEARCH_CASES_LHS", content_type_id=15)
        Permission.objects.create(codename="MAILSHOT_RECIPIENT", content_type_id=15)
        exporter = self.create_exporter()
        role_name = f"Exporter Contacts:Approve/Reject Agents and Exporters:{exporter.id}"
        permissions = Role.objects.get(name=role_name).permissions.all()
        self.assertEqual(len(permissions), 3)
        codenames = []
        for p in permissions:
            codenames.append(p.codename)
        self.assertTrue("IMP_CERT_AGENT_APPROVER" in codenames)
        self.assertTrue("IMP_CERT_SEARCH_CASES_LHS" in codenames)
        self.assertTrue("MAILSHOT_RECIPIENT" in codenames)

    def test_application_edit_role_created(self):
        exporter = self.create_exporter()
        role_name = f"Exporter Contacts:Edit Applications:{exporter.id}"
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_edit_role_has_default_permissions(self):
        Permission.objects.create(codename="IMP_CERT_EDIT_APPLICATION", content_type_id=15)
        Permission.objects.create(codename="IMP_CERT_SEARCH_CASES_LHS", content_type_id=15)
        Permission.objects.create(codename="MAILSHOT_RECIPIENT", content_type_id=15)
        exporter = self.create_exporter()
        role_name = f"Exporter Contacts:Edit Applications:{exporter.id}"
        permissions = Role.objects.get(name=role_name).permissions.all()
        self.assertEqual(len(permissions), 3)
        codenames = []
        for p in permissions:
            codenames.append(p.codename)
        self.assertTrue("IMP_CERT_EDIT_APPLICATION" in codenames)
        self.assertTrue("IMP_CERT_SEARCH_CASES_LHS" in codenames)
        self.assertTrue("MAILSHOT_RECIPIENT" in codenames)

    def test_application_view_role_created(self):
        exporter = self.create_exporter()
        role_name = f"Exporter Contacts:View Applications/Certificates:{exporter.id}"
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_view_role_has_default_permissions(self):
        Permission.objects.create(codename="IMP_CERT_VIEW_APPLICATION", content_type_id=15)
        Permission.objects.create(codename="IMP_CERT_SEARCH_CASES_LHS", content_type_id=15)
        Permission.objects.create(codename="MAILSHOT_RECIPIENT", content_type_id=15)
        exporter = self.create_exporter()
        role_name = f"Exporter Contacts:View Applications/Certificates:{exporter.id}"
        permissions = Role.objects.get(name=role_name).permissions.all()
        self.assertEqual(len(permissions), 3)
        codenames = []
        for p in permissions:
            codenames.append(p.codename)
        self.assertTrue("IMP_CERT_VIEW_APPLICATION" in codenames)
        self.assertTrue("IMP_CERT_SEARCH_CASES_LHS" in codenames)
        self.assertTrue("MAILSHOT_RECIPIENT" in codenames)
