import random

import factory
import factory.fuzzy
from faker import Faker

from web.domains.office.models import Office

fake = Faker("en_GB")


class OfficeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Office

    is_active = random.choice([True, False])
    address_1 = fake.address()[:35]
    address_2 = None
    address_3 = None
    address_4 = None
    address_5 = None
    postcode = fake.postcode()
