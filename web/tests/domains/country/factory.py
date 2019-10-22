import random

import factory
import factory.fuzzy
from web.domains.country.models import (Country, CountryGroup,
                                        CountryTranslation,
                                        CountryTranslationSet)


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Country

    name = factory.Faker('sentence', nb_words=2)
    is_active = random.choice([True, False])
    type = factory.fuzzy.FuzzyChoice(Country.TYPES, getter=lambda t: t[0])
    commission_code = factory.Faker('pystr', max_chars=20)
    hmrc_code = factory.Faker('pystr', max_chars=20)


class CountryGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CountryGroup

    name = factory.Faker('sentence', nb_words=2)
    comments = factory.Faker('paragraph', nb=2)
    countries = factory.Faker('pystr', max_chars=20)

    @factory.post_generation
    def countries(self, create, countries, **kwargs):
        if not create:
            return

        if countries:
            for country in countries:
                self.countries.add(country)


class CountryTranslationSetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CountryTranslationSet

    name = factory.Faker('sentence', nb_words=1)
    is_active = random.choice([True, False])


class CountryTranslationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CountryTranslation

    translation = factory.Faker('pystr', max_chars=10)
    country = factory.SubFactory(CountryFactory, is_active=True)
    translation_set = factory.SubFactory(CountryTranslationSetFactory,
                                         is_active=True)
