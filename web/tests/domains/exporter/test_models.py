from django.test import TestCase

from web.models import Exporter


class TestExporter(TestCase):
    def create_exporter(self, is_active=True, name="The Exporters Ltd."):
        return Exporter.objects.create(is_active=is_active, name=name)

    def test_create_exporter(self):
        exporter = self.create_exporter()
        assert isinstance(exporter, Exporter)
        assert exporter.name == "The Exporters Ltd."

    def test_archive_exporter(self):
        exporter = self.create_exporter()
        exporter.archive()
        assert exporter.is_active is False

    def test_unarchive_exporter(self):
        exporter = self.create_exporter(is_active=False)
        assert exporter.is_active is False
        exporter.unarchive()
        assert exporter.is_active is True
