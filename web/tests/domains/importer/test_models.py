from django.test import TestCase

from web.domains.importer.models import Importer


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
