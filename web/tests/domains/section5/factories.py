import factory

from web.models import Section5Clause


class Section5ClauseFactory(factory.django.DjangoModelFactory):
    is_active = True
    clause = factory.Sequence(lambda n: f"clause {n}")
    description = factory.Faker("paragraph", nb_sentences=2)

    class Meta:
        model = Section5Clause
