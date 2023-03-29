from django.test import TestCase

from web.domains.exporter.forms import ExporterFilter

from .factory import ExporterFactory


class ImporterFilterTest(TestCase):
    def setUp(self):
        ExporterFactory(name="Archived Exporter", is_active=False)
        ExporterFactory(name="Active Exporter", is_active=True)
        ExporterFactory(name="Another Archived Exporter", is_active=False)
        ExporterFactory(name="Another Active Exporter", is_active=True)

    def run_filter(self, data=None):
        return ExporterFilter(data=data).qs

    def test_name_filter(self):
        results = self.run_filter({"exporter_name": "active"})
        self.assertEqual(results.count(), 2)

    def test_filter_order(self):
        results = self.run_filter({"exporter_name": "exporter"})
        self.assertEqual(results.count(), 7)
        first = results.first()
        last = results.last()
        self.assertEqual(first.name, "Active Exporter")
        self.assertEqual(last.name, "Archived Exporter")
