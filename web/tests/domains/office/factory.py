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
    address = fake.address()
    postcode = None
