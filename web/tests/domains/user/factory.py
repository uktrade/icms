import factory
from web.domains.user.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = 'test_user'
    email = 'test@example.com'
    password = factory.PostGenerationMethodCall('set_password', 'test')
    is_superuser = False
    is_staff = True
    is_active = True
    register_complete = True
