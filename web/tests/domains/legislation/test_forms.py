import logging

from django.test import TestCase
from web.domains.legislation.forms import (ProductLegislationFilter,
                                           ProductLegislationForm)

logger = logging.getLogger(__name__)


class ProductLegislationFilterTest(TestCase):
    fixtures = ['web/fixtures/web/productlegislation.json']

    def run_filter(self, data=None):
        return ProductLegislationFilter(data=data).qs

    def test_name_filter(self):
        results = self.run_filter({'name': 'legislation'})
        self.assertEqual(results.count(), 3)

    def test_biocidal_filter(self):
        results = self.run_filter({'is_biocidal': False})
        self.assertEqual(results.count(), 1)
        first = results.first()
        self.assertEqual(first.name, 'Comprehensive legislation')

    def test_biocidal_claim_filter(self):
        results = self.run_filter({'is_biocidal_claim': True})
        self.assertEqual(results.count(), 1)
        first = results.first()
        self.assertEqual(first.name, 'Test Legislation')

    def test_is_cosmetics_regulation_filter(self):
        results = self.run_filter({'is_eu_cosmetics_regulation': True})
        self.assertEqual(results.count(), 2)

    def test_filter_order(self):
        results = self.run_filter({'name': 'legislation'})
        self.assertEqual(results.count(), 3)
        first = results.first()
        last = results.last()
        self.assertEqual(first.name, 'Comprehensive legislation')
        self.assertEqual(last.name, 'Test Legislation')


class ProductLegislationFormTest(TestCase):
    def test_form_valid(self):
        form = ProductLegislationForm(data={'name': 'Testing'})
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = ProductLegislationForm(data={})
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = ProductLegislationForm(data={})
        self.assertEqual(len(form.errors), 1)
        message = form.errors['name'][0]
        self.assertEqual(message, 'You must enter this item')
