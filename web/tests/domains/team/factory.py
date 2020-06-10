import factory
import factory.fuzzy

from web.domains.team.models import Role, Team


class TeamFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('sentence', nb_words=8)

    class Meta:
        model = Team


class RoleFactory(factory.django.DjangoModelFactory):

    name = f"Team:{factory.Faker('sentence', nb_words=2)}"
    description = factory.Faker('sentence', nb_words=8)
    role_order = 10
    team = factory.SubFactory(TeamFactory)

    class Meta:
        model = Role
