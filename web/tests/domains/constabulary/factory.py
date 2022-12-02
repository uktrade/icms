import random

import factory.fuzzy

from web.domains.constabulary.models import Constabulary


class ConstabularyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Constabulary

    name = factory.Faker("sentence", nb_words=2)
    region = factory.fuzzy.FuzzyChoice(Constabulary.REGIONS, getter=lambda r: r[0])
    email = factory.Sequence(lambda n: "constabulary%s@example.com" % n)  # /PS-IGNORE
    is_active = random.choice([True, False])
