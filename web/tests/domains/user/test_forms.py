import random

from django.test import TestCase

from web.domains.user.forms import (
    PeopleFilter,
    PhoneNumberForm,
    UserDetailsUpdateForm,
    UserListFilter,
)
from web.domains.user.models import PersonalEmail, PhoneNumber, User

from .factory import UserFactory


def run_filter(data=None):
    return UserListFilter(data=data).qs


class UserListFilterTest(TestCase):
    def setUp(self):
        # set default admin user password disposition as FULL
        UserFactory(
            username="aloy",
            is_active=True,
            email="aloy@example.com",
            first_name="Aloy",
            last_name="Unknown",
            organisation="Unknown",
            password_disposition=User.FULL,
            job_title="seeker",
            account_status=User.ACTIVE,
        )
        UserFactory(
            username="willem",
            is_active=True,
            email="willem@example.com",
            first_name="Willem",
            last_name="Unknown",
            organisation="Byrgenwerth College",
            password_disposition=User.TEMPORARY,
            job_title="Master",
            account_status=User.BLOCKED,
        )
        UserFactory(
            username="nathan.drake",
            is_active=True,
            email="nathan.drake@example.com",
            first_name="Nathan",
            last_name="Drake",
            organisation="N/A",
            password_disposition=User.TEMPORARY,
            job_title="explorer",
            account_status=User.SUSPENDED,
        )
        UserFactory(
            username="ori",
            is_active=True,
            email="ori@example.com",
            first_name="Ori",
            last_name="Unknown",
            organisation="Blind Forest",
            password_disposition=User.TEMPORARY,
            job_title="",
            account_status=User.CANCELLED,
        )
        UserFactory(
            username="mario",
            is_active=True,
            email="mario@example.com",
            first_name="Mario",
            last_name="Bro",
            organisation="Bros. Plumbers Ltd.",
            password_disposition=User.FULL,
            job_title="Chief Plumber",
            account_status=User.ACTIVE,
        )

    def run_filter(self, data=None):
        return UserListFilter(data=data).qs

    def test_email_filter(self):
        results = self.run_filter({"email_address": "example.com"})
        self.assertEqual(results.count(), 5)

    def test_username_filter(self):
        results = self.run_filter({"username": "willem"})
        self.assertEqual(results.count(), 1)

    def test_first_name_filter(self):
        results = self.run_filter({"forename": "nathan"})
        self.assertEqual(results.count(), 1)

    def test_last_name_filter(self):
        results = self.run_filter({"surname": "Unknown"})
        self.assertEqual(results.count(), 3)

    def test_organisation_filter(self):
        results = self.run_filter({"organisation": "Unk"})
        self.assertEqual(results.count(), 1)

    def test_job_title_filter(self):
        results = self.run_filter({"job_title": "plumber"})
        self.assertEqual(results.count(), 1)

    def test_account_status_filter(self):
        results = self.run_filter({"status": [User.CANCELLED, User.SUSPENDED, User.BLOCKED]})
        self.assertEqual(results.count(), 3)

    def test_password_disposition_filter(self):
        results = self.run_filter({"password_disposition": "on"})
        self.assertEqual(results.count(), 3)

    def test_filter_order(self):
        results = self.run_filter({"surname": "Unknown"})
        self.assertEqual(results.count(), 3)
        first = results.first()
        last = results.last()
        self.assertEqual(first.username, "aloy")
        self.assertEqual(last.username, "willem")


class PeopleFilterTest(TestCase):
    def create_email(self, user):
        email = PersonalEmail(user=user, email=f"{user.username}@example.com")
        email.save()
        return email

    def create_user(self, username, first_name, last_name, organisation, department, job_title):
        user = UserFactory(
            is_active=True,
            username=username,
            first_name=first_name,
            last_name=last_name,
            organisation=organisation,
            department=department,
            job_title=job_title,
        )
        user.personal_emails.add(self.create_email(user))

    def setUp(self):
        self.create_user(
            username="jane",
            first_name="Jane",
            last_name="Doe",
            organisation="Doe Ltd.",
            department="IT",
            job_title="Director",
        )
        self.create_user(
            username="john",
            first_name="John",
            last_name="Doe",
            organisation="Doe Ltd.",
            department="Finance",
            job_title="Accountant",
        )
        self.create_user(
            username="melkor",
            first_name="Melkor",
            last_name="Unknown",
            organisation="Evil Co.",
            department="One and only department",
            job_title="Ainur",
        )

    def run_filter(self, data=None):
        return PeopleFilter(data=data).qs

    def test_email_filter(self):
        results = self.run_filter({"email_address": "example.com"})
        self.assertEqual(results.count(), 3)

    def test_first_name_filter(self):
        results = self.run_filter({"forename": "melkor"})
        self.assertEqual(results.count(), 1)

    def test_last_name_filter(self):
        results = self.run_filter({"surname": "doe"})
        self.assertEqual(results.count(), 2)

    def test_organisation_filter(self):
        results = self.run_filter({"organisation": "ltd"})
        self.assertEqual(results.count(), 2)

    def test_department_filter(self):
        results = self.run_filter({"department": "on"})
        self.assertEqual(results.count(), 1)

    def test_job_title_filter(self):
        results = self.run_filter({"job": "direct"})
        self.assertEqual(results.count(), 1)

    def test_filter_order(self):
        results = self.run_filter({"email_address": "example"})
        self.assertEqual(results.count(), 3)
        first = results.first()
        last = results.last()
        self.assertEqual(first.username, "jane")
        self.assertEqual(last.username, "melkor")


class UserDetailsUpdateFormTest(TestCase):
    def test_form_valid(self):
        form = UserDetailsUpdateForm(
            data={
                "title": "Mx",
                "first_name": "Deniz",
                "last_name": "Last",
                "organisation": "DIT",
                "department": "DDaT",
                "job_title": "Developer",
                "work_address": "Windsor House",
                "date_of_birth": "13-Jan-1956",
                "security_question": "How are you?",
                "security_answer": "Fine",
                "security_answer_repeat": "Fine",
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_invalid(self):
        form = UserDetailsUpdateForm(data={})
        self.assertFalse(form.is_valid())

    def test_invalid_form_message(self):
        form = UserDetailsUpdateForm(
            data={
                "title": "Mx",
                "first_name": "Deniz",
                "last_name": "Last",
                "organisation": "DIT",
                "department": "DDaT",
                "work_address": "Windsor House",
                "date_of_birth": "13-Jan-1956",
                "security_question": "How are you?",
                "security_answer": "Fine",
                "security_answer_repeat": "Fine",
            }
        )
        self.assertEqual(len(form.errors), 1)
        message = form.errors["job_title"][0]
        self.assertEqual(message, "You must enter this item")

    def test_security_answer_validation(self):
        form = UserDetailsUpdateForm(
            data={"security_answer": "Hello", "security_answer_repeat": "Hi"}
        )
        message = form.errors["security_answer_repeat"][0]
        self.assertEqual(message, "Security answers do not match.")


class PhoneNumberFormTest(TestCase):
    def phone_number(self, number):
        return {
            "telephone_number": number,
            "type": random.choice(
                [
                    PhoneNumber.WORK,
                    PhoneNumber.FAX,
                    PhoneNumber.MOBILE,
                    PhoneNumber.HOME,
                    PhoneNumber.MINICOM,
                ]
            ),
        }

    def test_landline_phone_number_valid(self):
        form = PhoneNumberForm(data=self.phone_number("02012345678"))
        self.assertTrue(form.is_valid())
        form = PhoneNumberForm(data=self.phone_number("0201234 5678"))
        self.assertTrue(form.is_valid())
        form = PhoneNumberForm(data=self.phone_number("020 1234 5678"))
        self.assertTrue(form.is_valid())
        form = PhoneNumberForm(data=self.phone_number("020 12 345678"))
        self.assertTrue(form.is_valid())

    def test_mobile_phone_number_valid(self):
        form = PhoneNumberForm(data=self.phone_number("07123456789"))
        self.assertTrue(form.is_valid())
        form = PhoneNumberForm(data=self.phone_number("07123 456789"))
        self.assertTrue(form.is_valid())
        form = PhoneNumberForm(data=self.phone_number("07123 456 789"))
        self.assertTrue(form.is_valid())

    def test_international_phone_number_valid(self):
        form = PhoneNumberForm(data=self.phone_number("+902161234567"))
        self.assertTrue(form.is_valid())
        form = PhoneNumberForm(data=self.phone_number("00902161234567"))
        self.assertTrue(form.is_valid())
        form = PhoneNumberForm(data=self.phone_number("+90 216 1234567"))
        self.assertTrue(form.is_valid())
        form = PhoneNumberForm(data=self.phone_number("0090 216 1234567"))
        self.assertTrue(form.is_valid())
        form = PhoneNumberForm(data=self.phone_number("+90 216 123 4567"))
        self.assertTrue(form.is_valid())
        form = PhoneNumberForm(data=self.phone_number("+90 216 123 45 67"))
        self.assertTrue(form.is_valid())
