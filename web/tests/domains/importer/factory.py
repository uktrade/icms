import factory.fuzzy

from web.domains.importer.models import Importer
from web.tests.domains.user.factory import UserFactory


class ImporterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Importer

    is_active = True
    type = Importer.ORGANISATION
    region_origin = Importer.UK
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


class AgentImporterFactory(ImporterFactory):
    is_active = True
    main_importer = factory.SubFactory(ImporterFactory, is_active=True)

    @factory.post_generation
    def main_importer_offices(self, create, extracted, **kwargs):
        if not create:
            # Simple build
            return

        if extracted:
            # A list of offices passed in
            for office in extracted:
                self.main_importer.offices.add(office)
