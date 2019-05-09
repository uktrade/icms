from web.models import User
from django.db.utils import IntegrityError
import pytest


@pytest.mark.django_db
class TestUser:
    @pytest.fixture
    def sample_user(self):
        test_user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            first_name="Tester",
            last_name="Testing")
        test_user.set_password("TestPasS")
        test_user.save()
        return test_user

    def test_store_user(self, sample_user):
        users = User.objects.filter(username="tester")
        assert users

    def test_delete_user(self, sample_user):
        User.objects.filter(username="tester").delete()
        users = User.objects.filter(username="tester")
        assert not users

    def test_store_duplicate_username(self, sample_user):
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="tester", email="email@example.com").save()


class TestAccessRequest():
    pass


class TestAccessRequestProcess():
    pass


class TestOutboudEmail():
    pass


class TestEmailAttachment():
    pass
