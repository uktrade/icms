from django.test import TestCase

from web.models import Exporter


class TestExporter(TestCase):
    def create_exporter(self, is_active=True, name="The Exporters Ltd."):
        return Exporter.objects.create(is_active=is_active, name=name)

    def test_create_exporter(self):
        exporter = self.create_exporter()
        assert isinstance(exporter, Exporter)
        assert exporter.name == "The Exporters Ltd."
