from django.test import TestCase
from django.utils.timezone import datetime

from web.domains.commodity.forms import (
    CommodityFilter,
    CommodityForm,
    CommodityGroupFilter,
    CommodityGroupForm,
)
from web.models import Commodity, CommodityGroup, CommodityType, Unit

from .factory import CommodityFactory, CommodityGroupFactory


class CommodityFilterTest(TestCase):
    def setUp(self):
        commodity_type = CommodityType.objects.first()

        CommodityFactory(commodity_code="1234567", is_active=False, commodity_type=commodity_type)
        CommodityFactory(
            commodity_code="987654",
            is_active=True,
            validity_start_date=datetime(1986, 5, 17),
            validity_end_date=datetime(2050, 4, 12),
            commodity_type=commodity_type,
        )
        CommodityFactory(
            commodity_code="5151515151",
            is_active=True,
            validity_start_date=datetime(2051, 7, 18),
            validity_end_date=datetime(2055, 6, 19),
            commodity_type=commodity_type,
        )

    def run_filter(self, data=None):
        return CommodityFilter(data=data).qs

    def test_commodity_code_filter(self):
        results = self.run_filter({"commodity_code": "7654"})
        self.assertEqual(results.count(), 1)

    def test_archived_filter(self):
        results = self.run_filter({"is_archived": True})
        self.assertGreater(results.count(), 1)

    def test_validity_start_filter(self):
        results = self.run_filter({"validy_start": datetime(1985, 12, 12)})
        self.assertGreater(results.count(), 2)

    def test_validity_end_filter(self):
        results = self.run_filter({"valid_end": datetime(2051, 12, 12)})
        self.assertGreater(results.count(), 1)

    def test_filter_order(self):
        results = self.run_filter({"commodity_code": 5})
        self.assertGreater(results.count(), 2)


class CommodityFormTest(TestCase):
    def test_form_valid(self):
        code = "42"
        form = CommodityForm(
            data={
                "commodity_code": f"{code}34567890",
                "validity_start_date": "13-May-2020",
                "commodity_type": CommodityType.objects.first().pk,
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = CommodityForm(data={"commodity_code": "1234567890"})
        self.assertFalse(form.is_valid())

        self.assertEqual(len(form.errors), 2, form.errors)

        message = form.errors["validity_start_date"][0]
        self.assertEqual(message, "You must enter this item")


class CommodityGroupFilterTest(TestCase):
    def setUp(self):
        commodity_type = CommodityType.objects.first()
        CommodityGroupFactory(
            is_active=False,
            group_code="11",
            group_name="Group Archived",
            group_type=CommodityGroup.AUTO,
            group_description="Archived group",
        ).commodities.add(
            CommodityFactory(
                is_active=True, commodity_code="12345678", commodity_type=commodity_type
            )
        )
        CommodityGroupFactory(
            is_active=True,
            group_code="13",
            group_name="Active Group 1",
            group_type=CommodityGroup.CATEGORY,
            group_description="First active commodity group",
        ).commodities.add(
            CommodityFactory(is_active=True, commodity_code="987654", commodity_type=commodity_type)
        )
        CommodityGroupFactory(
            is_active=True,
            group_code="12z",
            group_name="Active Group 2",
            group_type=CommodityGroup.AUTO,
            group_description="Second active commodity group",
        ).commodities.add(
            CommodityFactory(
                is_active=True, commodity_code="5151515151", commodity_type=commodity_type
            )
        )

    def run_filter(self, data=None):
        return CommodityGroupFilter(data=data).qs

    def test_group_type_filter(self):
        results = self.run_filter({"group_type": CommodityGroup.AUTO, "group_name": "Group 2"})
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().group_code, "12z")

    def test_group_code_filter(self):
        results = self.run_filter({"group_code": "12z"})
        self.assertEqual(results.count(), 1)

    def test_archived_filter(self):
        results = self.run_filter({"is_archived": True})
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().group_code, "11")

    def test_group_name_filter(self):
        results = self.run_filter({"group_name": "Active"})
        self.assertEqual(results.count(), 2)

    def test_group_description_filter(self):
        results = self.run_filter({"group_description": "active"})
        self.assertEqual(results.count(), 2)

    def test_commodity_code_filter(self):
        results = self.run_filter({"commodity_code": "7654"})
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().group_code, "13")

    def test_filter_order(self):
        results = self.run_filter({"group_name": "active"})
        self.assertEqual(results.count(), 2)
        first = results.first()
        last = results.last()
        self.assertEqual(first.group_code, "12z")
        self.assertEqual(last.group_code, "13")


class CommodityGroupFormTest(TestCase):
    def test_form_valid(self):
        form = CommodityGroupForm(
            data={
                "group_type": CommodityGroup.AUTO,
                "commodity_type": CommodityType.objects.first().pk,
                "group_code": "1234",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid(self):
        form = CommodityGroupForm(
            data={
                "group_type": CommodityGroup.CATEGORY,
                "commodities": [Commodity.objects.first().pk],
                "unit": Unit.objects.first().pk,
            }
        )
        self.assertEqual(len(form.errors), 2, form.errors)
        message = form.errors["group_code"][0]
        self.assertEqual(message, "You must enter this item")
        message = form.errors["commodity_type"][0]
        self.assertEqual(message, "You must enter this item")
