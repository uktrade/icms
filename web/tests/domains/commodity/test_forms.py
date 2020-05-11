from django.test import TestCase
from django.utils.timezone import datetime

from web.domains.commodity.forms import CommodityFilter, CommodityForm

from .factory import CommodityFactory


class CommodityFilterTest(TestCase):
    def setUp(self):
        CommodityFactory(commodity_code='1234567', is_active=False)
        CommodityFactory(commodity_code='987654',
                         is_active=True,
                         validity_start_date=datetime(1986, 5, 17),
                         validity_end_date=datetime(2050, 4, 12))
        CommodityFactory(commodity_code='5151515151',
                         is_active=True,
                         validity_start_date=datetime(2051, 7, 18),
                         validity_end_date=datetime(2055, 6, 19))

    def run_filter(self, data=None):
        return CommodityFilter(data=data).qs

    def test_commodity_code_filter(self):
        results = self.run_filter({'commodity_code': '7654'})
        self.assertEqual(results.count(), 1)

    def test_archived_filter(self):
        results = self.run_filter({'is_archived': True})
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().commodity_code, '1234567')

    def test_validity_start_filter(self):
        results = self.run_filter({'validy_start': datetime(1985, 12, 12)})
        self.assertEqual(results.count(), 2)

    def test_validity_end_filter(self):
        results = self.run_filter({'valid_end': datetime(2051, 12, 12)})
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().commodity_code, '987654')

    def test_filter_order(self):
        results = self.run_filter({'commodity_code': 5})
        self.assertEqual(results.count(), 2)
        first = results.first()
        last = results.last()
        self.assertEqual(first.commodity_code, '5151515151')
        self.assertEqual(last.commodity_code, '987654')


class CommodityFormTest(TestCase):
    def test_form_valid(self):
        form = CommodityForm(data={
            'commodity_code': '987654',
            'validity_start_date': '13-May-2020'
        })
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = CommodityForm(data={'commodity_code': '2374267'})
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = CommodityForm(data={'commodity_code': '32134'})
        self.assertEqual(len(form.errors), 1)
        message = form.errors['validity_start_date'][0]
        self.assertEqual(message, 'You must enter this item')
