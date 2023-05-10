import random

from django.test import TestCase

from web.domains.user.forms import (
    PeopleFilter,
    PhoneNumberForm,
    UserDetailsUpdateForm,
    UserListFilter,
)
from web.models import PersonalEmail, PhoneNumber, User

from .factory import UserFactory


def run_filter(data=None):
    return UserListFilter(data=data).qs


class TestUserListFilter(TestCase):
    def setUp(self):
        # set default admin user password disposition as FULL
        UserFactory(
            username="aloy",
            is_active=True,
            email="aloy@example.com",  # /PS-IGNORE
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
            email="willem@example.com",  # /PS-IGNORE
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
            email="nathan.drake@example.com",  # /PS-IGNORE
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
            email="ori@example.com",  # /PS-IGNORE
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
            email="mario@example.com",  # /PS-IGNORE
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
        assert results.count() == 5

    def test_username_filter(self):
        results = self.run_filter({"username": "willem"})
        assert results.count() == 1

    def test_first_name_filter(self):
        results = self.run_filter({"forename": "nathan"})
        assert results.count() == 1

    def test_last_name_filter(self):
        results = self.run_filter({"surname": "Unknown"})
        assert results.count() == 3

    def test_organisation_filter(self):
        results = self.run_filter({"organisation": "Unk"})
        assert results.count() == 1

    def test_job_title_filter(self):
        results = self.run_filter({"job_title": "plumber"})
        assert results.count() == 1

    def test_account_status_filter(self):
        results = self.run_filter({"status": [User.CANCELLED, User.SUSPENDED, User.BLOCKED]})
        assert results.count() == 3

    def test_password_disposition_filter(self):
        results = self.run_filter({"password_disposition": "off"})
        assert results.count() == 3

    def test_filter_order(self):
        results = self.run_filter({"surname": "Unknown"})
        assert results.count() == 3
        first = results.first()
        last = results.last()
        assert first.username == "aloy"
        assert last.username == "willem"


class TestPeopleFilter(TestCase):
    def create_email(self, user):
        email = PersonalEmail(user=user, email=f"{user.username}@example.com")  # /PS-IGNORE
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
        assert results.count() == 9

    def test_first_name_filter(self):
        results = self.run_filter({"forename": "melkor"})
        assert results.count() == 1

    def test_last_name_filter(self):
        results = self.run_filter({"surname": "doe"})
        assert results.count() == 2

    def test_organisation_filter(self):
        results = self.run_filter({"organisation": "ltd"})
        assert results.count() == 2

    def test_department_filter(self):
        results = self.run_filter({"department": "on"})
        assert results.count() == 1

    def test_job_title_filter(self):
        results = self.run_filter({"job": "direct"})
        assert results.count() == 1

    def test_filter_order(self):
        results = self.run_filter({"email_address": "example"})
        assert results.count() == 9
        first = results.first()
        last = results.last()
        assert first.username == "E1_A1_main_contact"
        assert last.username == "melkor"


class TestUserDetailsUpdateForm(TestCase):
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
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = UserDetailsUpdateForm(data={})
        assert form.is_valid() is False

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
        assert len(form.errors) == 1
        message = form.errors["job_title"][0]
        assert message == "You must enter this item"

    def test_security_answer_validation(self):
        form = UserDetailsUpdateForm(
            data={"security_answer": "Hello", "security_answer_repeat": "Hi"}
        )
        message = form.errors["security_answer_repeat"][0]
        assert message == "Security answers do not match."


class TestPhoneNumberForm(TestCase):
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
        assert form.is_valid() is True
        form = PhoneNumberForm(data=self.phone_number("0201234 5678"))
        assert form.is_valid() is True
        form = PhoneNumberForm(data=self.phone_number("020 1234 5678"))
        assert form.is_valid() is True
        form = PhoneNumberForm(data=self.phone_number("020 12 345678"))
        assert form.is_valid() is True

    def test_mobile_phone_number_valid(self):
        form = PhoneNumberForm(data=self.phone_number("07123456789"))
        assert form.is_valid() is True
        form = PhoneNumberForm(data=self.phone_number("07123 456789"))
        assert form.is_valid() is True
        form = PhoneNumberForm(data=self.phone_number("07123 456 789"))
        assert form.is_valid() is True

    def test_international_phone_number_valid(self):
        form = PhoneNumberForm(data=self.phone_number("+902161234567"))
        assert form.is_valid() is True
        form = PhoneNumberForm(data=self.phone_number("00902161234567"))
        assert form.is_valid() is True
        form = PhoneNumberForm(data=self.phone_number("+90 216 1234567"))
        assert form.is_valid() is True
        form = PhoneNumberForm(data=self.phone_number("0090 216 1234567"))
        assert form.is_valid() is True
        form = PhoneNumberForm(data=self.phone_number("+90 216 123 4567"))
        assert form.is_valid() is True
        form = PhoneNumberForm(data=self.phone_number("+90 216 123 45 67"))
        assert form.is_valid() is True
