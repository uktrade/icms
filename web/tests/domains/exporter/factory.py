import factory
import random
from web.domains.exporter.models import Exporter


class ExporterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Exporter

    is_active = random.choice([True, False])
    name = factory.Faker("sentence", nb_words=4)
    main_exporter = None

    @factory.post_generation
    def offices(self, create, extracted, **kwargs):
        if not create:
            # Simple build
            return

        if extracted:
            # A list of offices passed in
            for office in extracted:
                self.offices.add(office)
