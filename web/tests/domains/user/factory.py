import random

import factory
import factory.fuzzy

from web.domains.user.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'User%s' % n)
    email = factory.LazyAttribute(lambda u: '%s@example.com' % u.username)
    first_name = factory.Faker('pystr', max_chars=20)
    last_name = factory.Faker('pystr', max_chars=20)
    title = factory.Faker('pystr', max_chars=5)
    password = factory.PostGenerationMethodCall('set_password', 'test')
    is_superuser = random.choice([True, False])
    is_staff = random.choice([True, False])
    is_active = random.choice([True, False])
    account_status = factory.fuzzy.FuzzyChoice(User.STATUSES,
                                               getter=lambda r: r[0])
    password_disposition = factory.fuzzy.FuzzyChoice(User.PASSWORD_DISPOSITION,
                                                     getter=lambda r: r[0])
