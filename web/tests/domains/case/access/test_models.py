import datetime
from datetime import date

from django.test import TestCase
from web.domains.case.access import models


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

    #  def test_biocidal_yes_no_label(self):
    #      product_legisation = self.create_legislation()
    #      self.assertEqual(product_legisation.is_biocidal_yes_no, 'No')
    #      product_legisation.is_biocidal = True
    #      self.assertEqual(product_legisation.is_biocidal_yes_no, 'Yes')
    #
    #  def test_biocidal_claim_yes_no_label(self):
    #      product_legisation = self.create_legislation()
    #      product_legisation.is_biocidal_claim = True
    #      self.assertEqual(product_legisation.is_biocidal_claim_yes_no, 'Yes')
    #
    #  def test_cosmetics_regulation_yes_no_label(self):
    #      product_legisation = self.create_legislation()
    #      self.assertEqual(product_legisation.is_eu_cosmetics_regulation_yes_no,
    #                       'Yes')
    #
    #  def test_string_representation(self):
    #      product_legisation = self.create_legislation()
    #      self.assertEqual(product_legisation.__str__(),
    #                       f'Product Legislation ({product_legisation.name})')
