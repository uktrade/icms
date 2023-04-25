from django.test import TestCase

from web.domains.exporter.forms import ExporterFilter

from .factory import ExporterFactory


class TestImporterFilter(TestCase):
    def setUp(self):
        ExporterFactory(name="Archived Exporter", is_active=False)
        ExporterFactory(name="Active Exporter", is_active=True)
        ExporterFactory(name="Another Archived Exporter", is_active=False)
        ExporterFactory(name="Another Active Exporter", is_active=True)

    def run_filter(self, data=None):
        return ExporterFilter(data=data).qs

    def test_name_filter(self):
        results = self.run_filter({"exporter_name": "active"})
        assert results.count() == 2

    def test_filter_order(self):
        results = self.run_filter({"exporter_name": "exporter"})
        assert results.count() == 7
        first = results.first()
        last = results.last()
        assert first.name == "Active Exporter"
        assert last.name == "Archived Exporter"
