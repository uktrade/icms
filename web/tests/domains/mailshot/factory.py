import factory

from web.models import Mailshot


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
    is_active = True
