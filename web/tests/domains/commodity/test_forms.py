import datetime as dt

from django.test import TestCase

from web.domains.commodity.forms import (
    CommodityFilter,
    CommodityForm,
    CommodityGroupFilter,
    CommodityGroupForm,
)
from web.models import Commodity, CommodityGroup, CommodityType, Unit

from .factory import CommodityFactory, CommodityGroupFactory


class TestCommodityFilter(TestCase):
    def setUp(self):
        commodity_type = CommodityType.objects.first()

        CommodityFactory(commodity_code="1234567", is_active=False, commodity_type=commodity_type)
        CommodityFactory(
            commodity_code="987654",
            is_active=True,
            validity_start_date=dt.datetime(1986, 5, 17, tzinfo=dt.UTC),
            validity_end_date=dt.datetime(2050, 4, 12, tzinfo=dt.UTC),
            commodity_type=commodity_type,
        )
        CommodityFactory(
            commodity_code="5151515151",
            is_active=True,
            validity_start_date=dt.datetime(2051, 7, 18, tzinfo=dt.UTC),
            validity_end_date=dt.datetime(2055, 6, 19, tzinfo=dt.UTC),
            commodity_type=commodity_type,
        )

    def run_filter(self, data=None):
        return CommodityFilter(data=data).qs

    def test_commodity_code_filter(self):
        results = self.run_filter({"commodity_code": "7654"})
        assert results.count() == 1

    def test_archived_filter(self):
        results = self.run_filter({"is_archived": True})
        assert results.count() == 1

    def test_validity_start_filter(self):
        results = self.run_filter({"validy_start": dt.datetime(1985, 12, 12, tzinfo=dt.UTC)})
        assert results.count() > 2

    def test_validity_end_filter(self):
        results = self.run_filter({"valid_end": dt.datetime(2051, 12, 12, tzinfo=dt.UTC)})
        assert results.count() > 1

    def test_filter_order(self):
        results = self.run_filter({"commodity_code": 5})
        assert results.count() > 2


class TestCommodityForm(TestCase):
    def test_form_valid(self):
        code = "42"
        form = CommodityForm(
            data={
                "commodity_code": f"{code}34567890",
                "validity_start_date": "13-May-2020",
                "commodity_type": CommodityType.objects.first().pk,
            }
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = CommodityForm(data={"commodity_code": "1234567890"})
        assert form.is_valid() is False

        assert len(form.errors) == 2, form.errors

        message = form.errors["validity_start_date"][0]
        assert message == "You must enter this item"


class TestCommodityGroupFilter(TestCase):
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
        assert results.count() == 1
        assert results.first().group_code == "12z"

    def test_group_code_filter(self):
        results = self.run_filter({"group_code": "12z"})
        assert results.count() == 1

    def test_archived_filter(self):
        results = self.run_filter({"is_archived": True})
        assert results.count() == 1
        assert results.first().group_code == "11"

    def test_group_name_filter(self):
        results = self.run_filter({"group_name": "Active"})
        assert results.count() == 2

    def test_group_description_filter(self):
        results = self.run_filter({"group_description": "active"})
        assert results.count() == 2

    def test_commodity_code_filter(self):
        results = self.run_filter({"commodity_code": "7654"})
        assert results.count() == 1
        assert results.first().group_code == "13"

    def test_filter_order(self):
        results = self.run_filter({"group_name": "active"})
        assert results.count() == 2
        first = results.first()
        last = results.last()
        assert first.group_code == "12z"
        assert last.group_code == "13"


class TestCommodityGroupForm(TestCase):
    def test_form_valid(self):
        form = CommodityGroupForm(
            data={
                "group_type": CommodityGroup.AUTO,
                "commodity_type": CommodityType.objects.first().pk,
                "group_code": "1234",
            }
        )
        assert form.is_valid(), form.errors

    def test_form_invalid(self):
        form = CommodityGroupForm(
            data={
                "group_type": CommodityGroup.CATEGORY,
                "commodities": [Commodity.objects.first().pk],
                "unit": Unit.objects.first().pk,
            }
        )
        assert len(form.errors) == 2, form.errors
        message = form.errors["group_code"][0]
        assert message == "You must enter this item"
        message = form.errors["commodity_type"][0]
        assert message == "You must enter this item"
