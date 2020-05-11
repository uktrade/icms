import datetime
from datetime import date

from django.test import TestCase
from web.domains.commodity.models import Commodity


class CommodityTest(TestCase):
    def create_commodity(self,
                         is_active=True,
                         commodity_code='12345678',
                         validity_start_date=date.today(),
                         validity_end_date=date.today() +
                         datetime.timedelta(days=10),
                         quantity_threshold=8,
                         sigl_product_type='xyz'):
        return Commodity.objects.create(
            is_active=is_active,
            commodity_code=commodity_code,
            validity_start_date=validity_start_date,
            validity_end_date=validity_end_date,
            quantity_threshold=quantity_threshold,
            sigl_product_type=sigl_product_type)

    def test_create_commodity(self):
        commodity = self.create_commodity()
        self.assertTrue(isinstance(commodity, Commodity))
        self.assertEqual(commodity.commodity_code, '12345678')

    def test_archive_commodity(self):
        commodity = self.create_commodity()
        commodity.archive()
        self.assertFalse(commodity.is_active)

    def test_unarchive_commodity(self):
        commodity = self.create_commodity()
        commodity.unarchive()
        self.assertTrue(commodity.is_active)
