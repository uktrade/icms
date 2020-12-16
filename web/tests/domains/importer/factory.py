import random

import factory
import factory.fuzzy

from web.domains.importer.models import Importer
from web.tests.domains.user.factory import UserFactory


class ImporterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Importer

    is_active = random.choice([True, False])
    type = factory.fuzzy.FuzzyChoice(Importer.TYPES, getter=lambda t: t[0])
    region_origin = factory.fuzzy.FuzzyChoice(Importer.REGIONS, getter=lambda r: r[0])
    name = factory.Faker("sentence", nb_words=4)
    main_importer = None
    user = None

    @factory.post_generation
    def offices(self, create, extracted, **kwargs):
        if not create:
            # Simple build
            return

        if extracted:
            # A list of offices passed in
            for office in extracted:
                self.offices.add(office)


class IndividualImporterFactory(ImporterFactory):
    class Meta:
        model = Importer

    is_active = True
    type = Importer.INDIVIDUAL
    user = factory.SubFactory(UserFactory, permission_codenames=["importer_access"])
