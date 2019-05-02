from web.models import User
import pytest


@pytest.mark.django_db
class TestUser():
    def setUp(self):
        User.objects.create_user(
            username="tester",
            email="tester@example.com",
            first_name="Tester",
            last_name="Testing")
        self.test_user.set_password("TestPasS")

    def test_store_user(self):
        user = User.objects.filter(username="tester")
        assert user is not None
