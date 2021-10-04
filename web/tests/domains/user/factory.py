import factory
import factory.fuzzy
from django.contrib.auth.models import Permission

from web.domains.user.models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "User%s" % n)
    email = factory.LazyAttribute(lambda u: "%s@example.com" % u.username)
    first_name = factory.Faker("pystr", max_chars=20)
    last_name = factory.Faker("pystr", max_chars=20)
    title = factory.Faker("pystr", max_chars=5)
    password = factory.PostGenerationMethodCall("set_password", "test")
    is_superuser = False
    is_staff = False
    is_active = True
    account_status = User.ACTIVE
    password_disposition = User.FULL

    @factory.post_generation
    def permission_codenames(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for codename in extracted:
                permission = Permission.objects.get(codename=codename)
                self.user_permissions.add(permission)


class ActiveUserFactory(UserFactory):
    account_status = User.ACTIVE
    is_active = True
    is_staff = False
    password_disposition = User.FULL
