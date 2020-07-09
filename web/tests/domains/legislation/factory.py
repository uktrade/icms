import factory
import random
from web.domains.legislation.models import ProductLegislation


class ProductLegislationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductLegislation

    name = factory.Faker("sentence", nb_words=8)
    is_active = random.choice([True, False])
    is_biocidal = random.choice([True, False])
    is_biocidal_claim = random.choice([True, False])
    is_eu_cosmetics_regulation = random.choice([True, False])
