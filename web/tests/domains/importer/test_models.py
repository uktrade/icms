from django.test import TestCase

from web.models import Importer


class TestImporter(TestCase):
    def create_importer(
        self,
        is_active=True,
        type=Importer.ORGANISATION,
        name="Very Best Importers Ltd.",
    ):
        return Importer.objects.create(is_active=is_active, type=type, name=name)

    def test_create_importer(self):
        importer = self.create_importer()
        assert isinstance(importer, Importer)
        assert importer.name == "Very Best Importers Ltd."
        assert importer.type == Importer.ORGANISATION

    def test_archive_importer(self):
        importer = self.create_importer()
        importer.archive()
        assert importer.is_active is False

    def test_unarchive_importer(self):
        importer = self.create_importer(is_active=False)
        assert importer.is_active is False
        importer.unarchive()
        assert importer.is_active is True
