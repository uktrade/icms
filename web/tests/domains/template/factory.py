import datetime as dt
import random

import factory.fuzzy
from faker import Faker

from web.models import Template

fake = Faker("en_GB")


class TemplateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Template

    start_datetime = fake.date_time_between(start_date="-1y", end_date="+1y", tzinfo=dt.UTC)
    end_datetime = factory.LazyAttribute(
        lambda t: fake.date_time_between(start_date=t.start_datetime, end_date="+2y", tzinfo=dt.UTC)
    )
    is_active = random.choice([True, False])
    template_name = factory.Faker("sentence", nb_words=4)
    template_title = factory.Faker("sentence", nb_words=3)
    template_content = factory.Faker("sentence", nb_words=8)
    template_type = Template.DECLARATION
    application_domain = factory.fuzzy.FuzzyChoice(Template.DOMAINS, getter=lambda d: d[0])
