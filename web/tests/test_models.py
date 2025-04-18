import pytest
from django.db.utils import IntegrityError

from web.models import User


@pytest.mark.django_db
class TestUser:
    @pytest.fixture
    def user(self):
        test_user = User.objects.create_user(
            username="tester",
            email="tester@example.com",  # /PS-IGNORE
            first_name="Tester",
            last_name="Testing",
        )
        test_user.set_password("TestPasS")
        test_user.save()
        return test_user

    def test_store_user(self, user):
        users = User.objects.filter(username="tester")
        assert users

    def test_delete_user(self, user):
        User.objects.filter(username="tester").delete()
        users = User.objects.filter(username="tester")
        assert not users

    def test_store_duplicate_username(self, user):
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username="tester", email="email@example.com"  # /PS-IGNORE
            ).save()
