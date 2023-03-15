import factory

from web.models import Mailshot
from web.tests.domains.user.factory import UserFactory


class MailshotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Mailshot

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("sentence")
    status = Mailshot.Statuses.DRAFT
    is_email = True
    is_retraction_email = True
    is_to_importers = True
    is_to_exporters = True
    created_by = factory.SubFactory(UserFactory)
    is_active = True
