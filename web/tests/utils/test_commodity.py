import datetime as dt

import pytest

from web.models import (
    Commodity,
    CommodityGroup,
    CommodityType,
    Country,
    ImportApplicationType,
    Usage,
)
from web.utils.commodity import (
    get_usage_commodities,
    get_usage_countries,
    get_usage_records,
)


@pytest.fixture
def next_jan():
    """A future date"""
    return dt.datetime(dt.date.today().year + 1, 1, 1, 12, 0)


@pytest.fixture
def wood_test_data(db):
    app_type = ImportApplicationType.objects.get(type="WD")
    wood_type = CommodityType.objects.get(type_code="WOOD")

    country = Country.objects.get(name="Afghanistan")
    afghanistan_group = commodity_group(
        wood_type, "group_for_afghanistan", "1234567890", "2345678901", "3456789012"
    )
    create_usage(app_type, country, group=afghanistan_group)

    country = Country.objects.get(name="Albania")
    albania_group = commodity_group(wood_type, "group_for_albania", "1234567890", "2345678901")
    create_usage(app_type, country, group=albania_group)

    country = Country.objects.get(name="Algeria")
    algeria_group = commodity_group(wood_type, "group_for_algeria", "1234567890", "2345678901")
    create_usage(app_type, country, group=algeria_group)


def test_get_usage_records_correctly_filter_invalid_records(wood_test_data, next_jan):
    """Tests checking several date fields are filtered correctly."""

    app_type = ImportApplicationType.objects.get(type="WD")
    wood_type = CommodityType.objects.get(type_code="WOOD")

    country = Country.objects.get(name="Argentina")
    invalid_group = CommodityGroup.objects.create(
        group_type=CommodityGroup.CATEGORY,
        group_code="invalid-group",
    )

    # Add an expired commodity to the group
    old_commodity = commodity(
        "9999999999",
        wood_type,
        dt.date(2019, 1, 1),
        validity_end_date=dt.date(2020, 1, 1),
    )
    invalid_group.commodities.add(old_commodity)
    create_usage(app_type, country, invalid_group)

    usage_records = get_usage_records(app_type=ImportApplicationType.Types.WOOD_QUOTA)
    assert usage_records.count() == 3, "Filter expired commodity"

    # Update the group to have a future commodity
    future_commodity = commodity("9999999999", wood_type, next_jan)
    invalid_group.commodities.add(future_commodity)

    assert (
        get_usage_records(app_type=ImportApplicationType.Types.WOOD_QUOTA).count() == 3
    ), "Filter future commodity"

    # Create an expired usage record
    country = Country.objects.get(name="Armenia")
    country_group = commodity_group(wood_type, "group_for_armenia", "123456987", "789654123")
    create_usage(app_type, country, country_group, end_date=dt.date(2020, 1, 1))

    assert (
        get_usage_records(app_type=ImportApplicationType.Types.WOOD_QUOTA).count() == 3
    ), "Filter expired usage"

    # Create a future usage record
    country = Country.objects.get(name="Australia")
    country_group = commodity_group(wood_type, "group_for_australia", "123456987", "789654123")
    create_usage(app_type, country, country_group, start_date=next_jan)

    assert (
        get_usage_records(app_type=ImportApplicationType.Types.WOOD_QUOTA).count() == 3
    ), "Filter future usage"


def test_get_usage_records_correctly_filter_inactive_records(wood_test_data):
    """Tests checking is_active fields are filtered correctly."""

    app_type = ImportApplicationType.objects.get(type="WD")
    wood_type = CommodityType.objects.get(type_code="WOOD")

    country = Country.objects.get(name="Argentina")
    valid_group = CommodityGroup.objects.create(
        group_type=CommodityGroup.CATEGORY,
        group_code="valid-group",
    )

    # Add an inactive commodity to the group
    inactive_commodity = commodity("9999999999", wood_type, dt.date(2019, 1, 1), is_active=False)
    valid_group.commodities.add(inactive_commodity)
    create_usage(app_type, country, valid_group)

    assert (
        get_usage_records(app_type=ImportApplicationType.Types.WOOD_QUOTA).count() == 3
    ), "Filters inactive commodity"

    # Add an inactive country group
    country = Country.objects.get(name="Azerbaijan")
    country_group = commodity_group(
        wood_type, "group_for_azerbaijan", "123456987", "789654123", is_active=False
    )
    create_usage(app_type, country, country_group)

    assert (
        get_usage_records(app_type=ImportApplicationType.Types.WOOD_QUOTA).count() == 3
    ), "Filters inactive group"


def test_get_usage_countries_gets_correct_records(wood_test_data):
    country_qs = get_usage_countries(ImportApplicationType.Types.WOOD_QUOTA)

    actual = [(c.pk, c.name) for c in country_qs]

    expected = [
        (Country.objects.get(name="Afghanistan").pk, "Afghanistan"),
        (Country.objects.get(name="Albania").pk, "Albania"),
        (Country.objects.get(name="Algeria").pk, "Algeria"),
    ]

    assert expected == actual


def test_get_usage_commodities_gets_correct_records(wood_test_data):
    usage_records = get_usage_records(app_type=ImportApplicationType.Types.WOOD_QUOTA)

    assert usage_records.count() == 3

    commodities = get_usage_commodities(usage_records)

    expected = sorted(
        [
            "1234567890",
            "1234567890",
            "1234567890",
            "2345678901",
            "2345678901",
            "2345678901",
            "3456789012",
        ]
    )
    actual = sorted([c.commodity_code for c in commodities])

    assert expected == actual


def commodity(
    commodity_code, commodity_type, validity_start_date, *, validity_end_date=None, is_active=True
):
    """Create a Commodity record"""

    return Commodity.objects.create(
        commodity_code=commodity_code,
        commodity_type=commodity_type,
        validity_start_date=validity_start_date,
        validity_end_date=validity_end_date,
        is_active=is_active,
    )


def commodity_group(commodity_type, group_code, *commodity_codes, is_active=True):
    """Create a commodity group linked to the supplied commodity codes."""

    valid_from = dt.date(2020, 1, 1)
    commodities = [commodity(code, commodity_type, valid_from) for code in commodity_codes]

    group = CommodityGroup.objects.create(
        group_type=CommodityGroup.CATEGORY, group_code=group_code, is_active=is_active
    )

    group.commodities.add(*commodities)

    return group


def create_usage(app_type, country, group, *, start_date=None, end_date=None):
    """Create a Usage record"""

    if start_date is None:
        start_date = dt.date.today()

    Usage.objects.create(
        application_type=app_type,
        country=country,
        commodity_group=group,
        start_date=start_date,
        end_date=end_date,
    )
