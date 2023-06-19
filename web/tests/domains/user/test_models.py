from django.test import TestCase

from web.models import User


class TestUser(TestCase):
    @staticmethod
    def create_user(
        title="Mr",
        username="VIP",
        organisation="House of Jon",
        department="Sales",
        job_title="CEO",
        location_at_address="Floor 18",
        work_address="Windsor House, 50 Victoria Street, London, SW1H 0TL",  # /PS-IGNORE
        date_of_birth="2000-01-01",
    ):
        return User.objects.create(
            title=title,
            username=username,
            organisation=organisation,
            department=department,
            job_title=job_title,
            location_at_address=location_at_address,
            work_address=work_address,
            date_of_birth=date_of_birth,
        )

    def test_create_user(self):
        user = self.create_user()
        assert isinstance(user, User)

    def test_username(self):
        user = self.create_user()
        assert user.username == "VIP"
