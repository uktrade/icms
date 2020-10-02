from django.test import TestCase

from web.domains.exporter.models import Exporter


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
