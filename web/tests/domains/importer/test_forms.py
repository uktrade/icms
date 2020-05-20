from django.test import TestCase
from web.domains.importer.forms import (ImporterFilter)
from web.domains.importer.models import Importer

from .factory import ImporterFactory


class ImporterFilterTest(TestCase):
    def setUp(self):
        ImporterFactory(name='Archived Importer Organisation',
                        type=Importer.ORGANISATION,
                        is_active=False)
        ImporterFactory(name='Active Importer Organisation',
                        type=Importer.ORGANISATION,
                        is_active=True)
        ImporterFactory(name='Archived Individual Importer',
                        type=Importer.INDIVIDUAL,
                        is_active=False)
        ImporterFactory(name='Active Individual Importer',
                        type=Importer.INDIVIDUAL,
                        is_active=True)

    def run_filter(self, data=None):
        return ImporterFilter(data=data).qs

    def test_name_filter(self):
        results = self.run_filter({'name': 'org'})
        self.assertEqual(results.count(), 2)

    def test_entity_type_filter(self):
        results = self.run_filter(
            {'importer_entity_type': Importer.INDIVIDUAL})
        self.assertEqual(results.count(), 2)

    def test_filter_order(self):
        results = self.run_filter({'name': 'import'})
        self.assertEqual(results.count(), 4)
        first = results.first()
        last = results.last()
        self.assertEqual(first.name, 'Active Importer Organisation')
        self.assertEqual(last.name, 'Archived Individual Importer')
