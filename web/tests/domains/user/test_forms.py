import random

from django.test import TestCase

from web.domains.user.forms import (
    OneLoginNewUserUpdateForm,
    UserDetailsUpdateForm,
    UserListFilter,
    UserPhoneNumberForm,
)
from web.models import PhoneNumber
from web.one_login.constants import ONE_LOGIN_UNSET_NAME

TOTAL_TEST_USERS = 20


class TestUserListFilter(TestCase):
    def run_filter(self, data=None):
        return UserListFilter(data=data).qs

    def test_email_filter(self):
        results = self.run_filter({"email_address": "example.com"})
        assert results.count() == TOTAL_TEST_USERS

    def test_username_filter(self):
        results = self.run_filter({"username": "I1_main_contact"})
        assert results.count() == 1

    def test_first_name_filter(self):
        results = self.run_filter({"forename": "I1_main_contact_first_name"})
        assert results.count() == 1

    def test_last_name_filter(self):
        results = self.run_filter({"surname": "main_contact"})
        assert results.count() == 6

    def test_organisation_filter(self):
        results = self.run_filter({"organisation": "I1_main_contact"})
        assert results.count() == 1

    def test_job_title_filter(self):
        results = self.run_filter({"job_title": "I1_main_contact_job_title"})
        assert results.count() == 1

    def test_filter_order(self):
        results = self.run_filter({"surname": "inactive"})
        assert results.count() == 4
        first = results.first()
        last = results.last()
        assert first.username == "E1_inactive_contact"
        assert last.username == "I3_inactive_contact"


class TestUserDetailsUpdateForm(TestCase):
    def test_form_valid(self):
        form = UserDetailsUpdateForm(
            initial={
                "email": "emaill@example.com",  # /PS-IGNORE
            },
            data={
                "title": "Mx",
                "first_name": "Deniz",
                "last_name": "Last",
                "organisation": "DIT",
                "department": "DDaT",
                "job_title": "Developer",
                "work_address": "Windsor House",
                "date_of_birth": "13-Jan-1956",
            },
        )
        assert form.is_valid() is True

    def test_form_invalid(self):
        form = UserDetailsUpdateForm(data={})
        assert form.is_valid() is False

    def test_invalid_form_message(self):
        form = UserDetailsUpdateForm(
            initial={
                "email": "emaill@example.com",  # /PS-IGNORE
            },
            data={
                "title": "Mx",
                "first_name": "",
                "last_name": "Last",
                "organisation": "DIT",
                "department": "DDaT",
                "work_address": "Windsor House",
                "date_of_birth": "13-Jan-1956",
            },
        )
        assert len(form.errors) == 1
        message = form.errors["first_name"][0]
        assert message == "You must enter this item"


class TestUserPhoneNumberForm(TestCase):
    def phone_number(self, number):
        return {
            "phone": number,
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
        form = UserPhoneNumberForm(data=self.phone_number("02012345678"))
        assert form.is_valid() is True
        form = UserPhoneNumberForm(data=self.phone_number("0201234 5678"))
        assert form.is_valid() is True
        form = UserPhoneNumberForm(data=self.phone_number("020 1234 5678"))
        assert form.is_valid() is True
        form = UserPhoneNumberForm(data=self.phone_number("020 12 345678"))
        assert form.is_valid() is True

    def test_mobile_phone_number_valid(self):
        form = UserPhoneNumberForm(data=self.phone_number("07123456789"))
        assert form.is_valid() is True
        form = UserPhoneNumberForm(data=self.phone_number("07123 456789"))
        assert form.is_valid() is True
        form = UserPhoneNumberForm(data=self.phone_number("07123 456 789"))
        assert form.is_valid() is True

    def test_international_phone_number_valid(self):
        form = UserPhoneNumberForm(data=self.phone_number("+902161234567"))
        assert form.is_valid() is True
        form = UserPhoneNumberForm(data=self.phone_number("00902161234567"))
        assert form.is_valid() is True
        form = UserPhoneNumberForm(data=self.phone_number("+90 216 1234567"))
        assert form.is_valid() is True
        form = UserPhoneNumberForm(data=self.phone_number("0090 216 1234567"))
        assert form.is_valid() is True
        form = UserPhoneNumberForm(data=self.phone_number("+90 216 123 4567"))
        assert form.is_valid() is True
        form = UserPhoneNumberForm(data=self.phone_number("+90 216 123 45 67"))
        assert form.is_valid() is True


class TestOneLoginNewUserUpdateForm:
    def test_form_errors_when_first_name_is_unset(self, importer_one_contact):
        importer_one_contact.first_name = ONE_LOGIN_UNSET_NAME
        importer_one_contact.save()

        form = OneLoginNewUserUpdateForm(initial={}, instance=importer_one_contact)

        assert form["first_name"].initial == ""
        assert form["last_name"].initial == importer_one_contact.last_name

    def test_form_sets_correct_initial_data_for_last_name(self, importer_one_contact):
        importer_one_contact.last_name = ONE_LOGIN_UNSET_NAME
        importer_one_contact.save()

        form = OneLoginNewUserUpdateForm(initial={}, instance=importer_one_contact)

        assert form["first_name"].initial == importer_one_contact.first_name
        assert form["last_name"].initial == ""
