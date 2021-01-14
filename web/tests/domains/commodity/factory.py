import random

import factory
import factory.fuzzy
import pytz
from faker import Faker

from web.domains.commodity.models import Commodity, CommodityGroup, CommodityType, Unit

fake = Faker("en_GB")


class CommodityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Commodity

    is_active = True
    start_datetime = fake.date_time_between(start_date="-2y", end_date="+1y", tzinfo=pytz.UTC)
    end_datetime = factory.LazyAttribute(
        lambda c: fake.date_time_between(
            start_date=c.start_datetime, end_date="+2y", tzinfo=pytz.UTC
        )
    )
    commodity_code = factory.fuzzy.FuzzyText(length=10)
    commodity_type = factory.SubFactory(
        "web.tests.domains.commodity.factory.CommodityTypeFactory",
        allowed_codes=[factory.SelfAttribute("commodity_code[:2]")],
    )
    validity_start_date = fake.date_between(start_date="-1y", end_date="+1y")
    validity_end_date = factory.LazyAttribute(
        lambda c: fake.date_between(start_date=c.validity_start_date, end_date="+2y")
    )
    quantity_threshold = factory.fuzzy.FuzzyInteger(0, 1000000000)
    sigl_product_type = factory.fuzzy.FuzzyText(length=3)


class CommodityGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommodityGroup

    is_active = random.choice([True, False])
    start_datetime = fake.date_time_between(start_date="-3y", end_date="+2y", tzinfo=pytz.UTC)
    end_datetime = factory.LazyAttribute(
        lambda c: fake.date_time_between(
            start_date=c.start_datetime, end_date="+3y", tzinfo=pytz.UTC
        )
    )
    group_type = random.choice([CommodityGroup.AUTO, CommodityGroup.CATEGORY])
    group_code = factory.fuzzy.FuzzyText(length=4)
    group_name = factory.Faker("sentence", nb_words=3)
    group_description = factory.Faker("sentence", nb_words=7)


class CommodityTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommodityType

    allowed_codes = [42]
    type = factory.Faker("sentence", nb_words=2)


class UnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Unit

    unit_type = factory.LazyAttribute(lambda x: "unit_{pk}")
    description = factory.LazyAttribute(lambda x: "description {pk}")
    short_description = factory.LazyAttribute(lambda x: "short description {pk}")
    hmrc_code = 42
