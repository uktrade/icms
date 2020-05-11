import random

import factory
import factory.fuzzy
from faker import Faker
from web.domains.commodity.models import Commodity

fake = Faker('en_GB')


class CommodityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Commodity

    is_active = random.choice([True, False])
    start_datetime = fake.date_time_between(start_date="-2y", end_date="+1y")
    end_datetime = factory.LazyAttribute(lambda c: fake.date_time_between(
        start_date=c.start_datetime, end_date="+2y"))
    commodity_code = factory.fuzzy.FuzzyInteger(1000000000, 3000000000)
    validity_start_date = fake.date_between(start_date="-1y", end_date="+1y")
    validity_end_date = factory.LazyAttribute(lambda c: fake.date_between(
        start_date=c.validity_start_date, end_date="+2y"))
    quantity_threshold = factory.fuzzy.FuzzyInteger(0, 1000000000)
    sigl_product_type = factory.fuzzy.FuzzyText(length=3)
