from django.contrib.auth.models import Permission
from django.test import TestCase

from web.domains.exporter.models import Exporter
from web.domains.team.models import Role


class ExporterTest(TestCase):
    def create_exporter(self, is_active=True, name='The Exporters Ltd.'):
        return Exporter.objects.create(is_active=is_active, name=name)

    def test_create_exporter(self):
        exporter = self.create_exporter()
        self.assertTrue(isinstance(exporter, Exporter))
        self.assertEqual(exporter.name, 'The Exporters Ltd.')

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
        role_name = f'Exporter Contacts:Approve/Reject Agents and Exporters:{exporter.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_agent_approve_reject_role_permissions_created(self):
        exporter = self.create_exporter()
        codename = f'IMP_EXPORTER_CONTACTS:AGENT_APPROVER:{exporter.id}:IMP_CERT_AGENT_APPROVER'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:AGENT_APPROVER:{exporter.id}:IMP_CERT_SEARCH_CASES_LHS'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:AGENT_APPROVER:{exporter.id}:MAILSHOT_RECIPIENT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())

    def test_application_edit_role_created(self):
        exporter = self.create_exporter()
        role_name = f'Exporter Contacts:Edit Applications:{exporter.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_edit_role_permissions_created(self):
        exporter = self.create_exporter()
        codename = f'IMP_EXPORTER_CONTACTS:EDIT_APPLICATION:{exporter.id}:MAILSHOT_RECIPIENT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:EDIT_APPLICATION:{exporter.id}:IMP_CERT_SEARCH_CASES_LHS'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:EDIT_APPLICATION:{exporter.id}:IMP_CERT_EDIT_APPLICATION'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())

    def test_application_view_role_created(self):
        exporter = self.create_exporter()
        role_name = f'Exporter Contacts:View Applications/Certificates:{exporter.id}'
        self.assertTrue(Role.objects.filter(name=role_name).exists())

    def test_application_view_role_permissions_created(self):
        exporter = self.create_exporter()
        codename = f'IMP_EXPORTER_CONTACTS:VIEW_APPLICATION:{exporter.id}:MAILSHOT_RECIPIENT'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:VIEW_APPLICATION:{exporter.id}:IMP_CERT_VIEW_APPLICATION'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
        codename = f'IMP_EXPORTER_CONTACTS:VIEW_APPLICATION:{exporter.id}:IMP_CERT_SEARCH_CASES_LHS'
        self.assertTrue(Permission.objects.filter(codename=codename).exists())
