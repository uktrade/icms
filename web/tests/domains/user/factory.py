import factory.fuzzy

from web.models import User


# TODO: ICMSLST-1984 Remove User factories and replace with users in web/tests/conftest.py
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "User%s" % n)
    email = factory.LazyAttribute(lambda u: "%s@example.com" % u.username)  # /PS-IGNORE
    first_name = factory.Faker("pystr", max_chars=20)
    last_name = factory.Faker("pystr", max_chars=20)
    title = factory.Faker("pystr", max_chars=5)
    password = factory.PostGenerationMethodCall("set_password", "test")
    is_superuser = False
    is_staff = False
    is_active = True
    account_status = User.ACTIVE
    password_disposition = User.FULL
