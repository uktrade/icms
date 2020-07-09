import factory
import factory.fuzzy
import random
from web.domains.office.models import Office

from faker import Faker

fake = Faker("en_GB")


class OfficeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Office

    is_active = random.choice([True, False])
    address = fake.address()
    postcode = None
