import factory
import factory.fuzzy
import random
from web.domains.importer.models import Importer


class ImporterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Importer

    is_active = random.choice([True, False])
    type = factory.fuzzy.FuzzyChoice(Importer.TYPES, getter=lambda t: t[0])
    name = factory.Faker('sentence', nb_words=4)
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
