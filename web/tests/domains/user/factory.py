import random

import factory
from web.domains.user.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'User%s' % n)
    email = factory.LazyAttribute(lambda u: '%s@example.com' % u.username)
    password = factory.PostGenerationMethodCall('set_password', 'test')
    is_superuser = random.choice([True, False])
    is_staff = random.choice([True, False])
    is_active = random.choice([True, False])
    password_disposition = random.choice([User.FULL, User.TEMPORARY])
