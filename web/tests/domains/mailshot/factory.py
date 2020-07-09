import random

import factory
import factory.fuzzy

from web.domains.mailshot.models import Mailshot
from web.tests.domains.user.factory import UserFactory


class MailshotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Mailshot

    title = factory.Faker("sentence", nb_words=4)
    description = factory.Faker("sentence")
    status = factory.fuzzy.FuzzyChoice(Mailshot.STATUSES, getter=lambda r: r[0])
    is_email = random.choice([True, False])
    is_retraction_email = random.choice([True, False])
    is_to_importers = random.choice([True, False])
    is_to_exporters = random.choice([True, False])
    created_by = factory.SubFactory(UserFactory)
    is_active = random.choice([True, False])
