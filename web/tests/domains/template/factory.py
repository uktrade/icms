import random

import factory
import factory.fuzzy
from faker import Faker
from web.domains.template.models import Template
import pytz

fake = Faker('en_GB')


class TemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Template

    start_datetime = fake.date_time_between(start_date="-1y", end_date="+1y", tzinfo=pytz.UTC)
    end_datetime = factory.LazyAttribute(lambda t: fake.date_time_between(
        start_date=t.start_datetime, end_date="+2y", tzinfo=pytz.UTC))
    is_active = random.choice([True, False])
    template_name = factory.Faker('sentence', nb_words=4)
    template_type = factory.fuzzy.FuzzyChoice(Template.TYPES,
                                              getter=lambda t: t[0])
    application_domain = factory.fuzzy.FuzzyChoice(Template.DOMAINS,
                                                   getter=lambda d: d[0])
