from django.test import TestCase

from web.models import User


class UserTest(TestCase):
    @staticmethod
    def create_user(
        title="Mr",
        username="VIP",
        middle_initials="G",
        organisation="House of Jon",
        department="Sales",
        job_title="CEO",
        location_at_address="Floor 18",
        work_address="Windsor House, 50 Victoria Street, London, SW1H 0TL",  # /PS-IGNORE
        date_of_birth="2000-01-01",
        security_question="Favorite term",
        security_answer="Retroactive rationalisation",
        share_contact_details=True,
        account_status=User.NEW,
        account_status_date="2019-01-01",
        password_disposition=User.FULL,
    ):
        return User.objects.create(
            title=title,
            username=username,
            middle_initials=middle_initials,
            organisation=organisation,
            department=department,
            job_title=job_title,
            location_at_address=location_at_address,
            work_address=work_address,
            date_of_birth=date_of_birth,
            security_question=security_question,
            security_answer=security_answer,
            share_contact_details=share_contact_details,
            account_status=account_status,
            account_status_date=account_status_date,
            password_disposition=password_disposition,
        )

    def test_create_user(self):
        user = self.create_user()
        self.assertTrue(isinstance(user, User))

    def test_username(self):
        user = self.create_user()
        self.assertEqual(user.username, "VIP")

    def test_set_temp_pass_changes_password(self):
        user = self.create_user()
        old_password = user.password
        user.set_temp_password()
        self.assertNotEqual(user.password, old_password)

    def test_set_temp_pass_sets_temp_password_disposition(self):
        user = self.create_user()
        user.password_disposition = User.FULL
        user.set_temp_password()
        self.assertEqual(user.password_disposition, User.TEMPORARY)
