import random

import factory
import factory.fuzzy
from web.domains.firearms.models import ObsoleteCalibre, ObsoleteCalibreGroup


class ObsoleteCalibreGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ObsoleteCalibreGroup

    name = factory.fuzzy.FuzzyText(length=6)
    is_active = random.choice([True, False])
    order = factory.Sequence(lambda n: n)


class ObsoleteCalibreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ObsoleteCalibre

    name = factory.fuzzy.FuzzyText(length=5)
    is_active = random.choice([True, False])
    order = factory.Sequence(lambda n: n)
    calibre_group = factory.SubFactory(ObsoleteCalibreGroupFactory,
                                       is_active=True)
