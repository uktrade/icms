import datetime
from datetime import date

from django.test import TestCase

from web.domains.commodity.models import Commodity, CommodityGroup
from web.tests.domains.commodity.factory import CommodityFactory, CommodityGroupFactory


class CommodityTest(TestCase):
    def create_commodity(
        self,
        is_active=True,
        commodity_code="1234567890",
        validity_start_date=date.today(),
        validity_end_date=date.today() + datetime.timedelta(days=10),
        quantity_threshold=8,
        sigl_product_type="xyz",
    ):
        return CommodityFactory.create(
            is_active=is_active,
            commodity_code=commodity_code,
            validity_start_date=validity_start_date,
            validity_end_date=validity_end_date,
            quantity_threshold=quantity_threshold,
            sigl_product_type=sigl_product_type,
        )

    def test_create_commodity(self):
        commodity = self.create_commodity()
        self.assertTrue(isinstance(commodity, Commodity))
        self.assertEqual(commodity.commodity_code, "1234567890")

    def test_archive_commodity(self):
        commodity = self.create_commodity()
        commodity.archive()
        self.assertFalse(commodity.is_active)

    def test_unarchive_commodity(self):
        commodity = self.create_commodity()
        commodity.unarchive()
        self.assertTrue(commodity.is_active)


class CommodityGroupTest(TestCase):
    def create_commodity_group(
        self,
        is_active=True,
        group_type=CommodityGroup.AUTO,
        group_code="12",
        group_name="Test group",
        group_description="Test group description",
        start_datetime=date.today(),
        end_datetime=date.today() + datetime.timedelta(days=20),
    ):
        return CommodityGroupFactory.create(
            is_active=is_active,
            group_type=group_type,
            group_code=group_code,
            group_description=group_description,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

    def test_create_commodity_group(self):
        commodity_group = self.create_commodity_group()
        self.assertTrue(isinstance(commodity_group, CommodityGroup))
        self.assertEqual(commodity_group.group_code, "12")

    def test_archive_commodity_group(self):
        commodity_group = self.create_commodity_group()
        commodity_group.archive()
        self.assertFalse(commodity_group.is_active)

    def test_unarchive_commodity_group(self):
        commodity_group = self.create_commodity_group()
        commodity_group.unarchive()
        self.assertTrue(commodity_group.is_active)
