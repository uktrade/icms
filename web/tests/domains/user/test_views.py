from http import HTTPStatus
from typing import Any

import pytest
from django.urls import reverse
from pytest_django.asserts import assertContains, assertRedirects

from web.forms.fields import JQUERY_DATE_FORMAT
from web.mail.constants import EmailTypes
from web.models import Email, PhoneNumber, User
from web.one_login.constants import ONE_LOGIN_UNSET_NAME
from web.sites import SiteName, get_exporter_site_domain
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.helpers import (
    check_gov_notify_email_was_sent,
    get_messages_from_response,
)


class TestUserUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, importer_one_contact, exporter_client, exporter_one_contact):
        self.importer_user = importer_one_contact
        self.exporter_user = exporter_one_contact

        self.importer_url = reverse("user-edit", kwargs={"user_pk": importer_one_contact.pk})
        self.exporter_url = reverse("user-edit", kwargs={"user_pk": exporter_one_contact.pk})

        self.importer_client = importer_client
        self.exporter_client = exporter_client

    def test_permission(self):
        response = self.importer_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.OK

    def _get_post_data(self, user: User, **overrides: Any) -> dict[str, Any]:
        return {
            "title": user.title or "",
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "organisation": user.organisation or "",
            "department": user.department or "",
            "job_title": user.job_title or "",
            "location_at_address": user.location_at_address or "",
            "work_address": user.work_address or "",
            "date_of_birth": user.date_of_birth.strftime(JQUERY_DATE_FORMAT),
        } | overrides


class TestNewUserUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, importer_one_contact, exporter_client, exporter_one_contact):
        self.importer_user = importer_one_contact
        self.exporter_user = exporter_one_contact

        self.importer_url = reverse("new-user-edit")
        self.exporter_url = reverse("new-user-edit")

        self.importer_client = importer_client
        self.exporter_client = exporter_client

    def test_new_one_login_user_redirects_to_importer_access_requests(self):
        self.importer_user.first_name = ONE_LOGIN_UNSET_NAME
        self.importer_user.save()

        form_data = {"first_name": "Bob", "last_name": self.importer_user.last_name}
        response = self.importer_client.post(self.importer_url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("access:importer-request")

    def test_new_one_login_user_redirects_to_exporter_access_requests(self):
        self.exporter_user.first_name = ONE_LOGIN_UNSET_NAME
        self.exporter_user.save()

        form_data = {"first_name": "Bob", "last_name": self.exporter_user.last_name}
        response = self.exporter_client.post(self.exporter_url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("access:exporter-request")


class TestUserCreateTelephoneView:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, importer_one_contact, exporter_client, exporter_one_contact):
        self.importer_url = reverse("user-number-add", kwargs={"user_pk": importer_one_contact.pk})
        self.exporter_url = reverse("user-number-add", kwargs={"user_pk": exporter_one_contact.pk})

        self.importer_client = importer_client
        self.exporter_client = exporter_client

    def test_permission(self):
        response = self.importer_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.OK


class TestUserUpdateTelephoneView:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, importer_one_contact, exporter_client, exporter_one_contact):
        self.importer_phone = add_user_phone(importer_one_contact, "01122 334455")
        self.exporter_phone = add_user_phone(exporter_one_contact, "01122 554433")

        self.importer_url = reverse(
            "user-number-edit",
            kwargs={"user_pk": importer_one_contact.pk, "phonenumber_pk": self.importer_phone.pk},
        )
        self.exporter_url = reverse(
            "user-number-edit",
            kwargs={"user_pk": exporter_one_contact.pk, "phonenumber_pk": self.exporter_phone.pk},
        )

        self.importer_client = importer_client
        self.exporter_client = exporter_client

    def test_permission(self):
        response = self.importer_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.OK


class TestUserDeleteTelephoneView:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, importer_one_contact, exporter_client, exporter_one_contact):
        self.importer_phone = add_user_phone(importer_one_contact, "01122 334455")
        self.exporter_phone = add_user_phone(exporter_one_contact, "01122 554433")

        self.importer_url = reverse(
            "user-number-delete",
            kwargs={"user_pk": importer_one_contact.pk, "phonenumber_pk": self.importer_phone.pk},
        )
        self.exporter_url = reverse(
            "user-number-delete",
            kwargs={"user_pk": exporter_one_contact.pk, "phonenumber_pk": self.exporter_phone.pk},
        )

        self.importer_client = importer_client
        self.exporter_client = exporter_client

    def test_permission(self):
        response = self.importer_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.importer_client.post(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.exporter_url)
        assert response.status_code == HTTPStatus.FOUND


class TestUserCreateEmailView:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, importer_one_contact, exporter_client, exporter_one_contact):
        self.importer_one_contact = importer_one_contact
        self.importer_url = reverse("user-email-add", kwargs={"user_pk": importer_one_contact.pk})
        self.exporter_url = reverse("user-email-add", kwargs={"user_pk": exporter_one_contact.pk})

        self.importer_client = importer_client
        self.exporter_client = exporter_client

    def test_permission(self):
        response = self.importer_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.OK

    def test_add_email_address_primary_true(self):
        assert self.importer_one_contact.emails.filter(is_primary=True).count() == 1
        data = {
            "email": "test@example.com",  # /PS-IGNORE
            "type": "WORK",
            "is_primary": True,
        }
        response = self.importer_client.post(self.importer_url, data=data)
        assert response.status_code == HTTPStatus.FOUND
        assert (
            self.importer_one_contact.emails.get(is_primary=True).email
            == "test@example.com"  # /PS-IGNORE
        )

    def test_add_email_address_primary_false(self):
        assert self.importer_one_contact.emails.filter(is_primary=True).count() == 1
        data = {
            "email": "test@example.com",  # /PS-IGNORE
            "type": "WORK",
            "is_primary": False,
        }
        response = self.importer_client.post(self.importer_url, data=data)
        assert response.status_code == HTTPStatus.FOUND
        assert (
            self.importer_one_contact.emails.get(is_primary=True).email
            == "I1_main_contact@example.com"  # /PS-IGNORE
        )

    def test_add_email_address_no_primary_set(self):
        email = self.importer_one_contact.emails.get(is_primary=True)
        email.is_primary = False
        email.save()

        data = {
            "email": "test@example.com",  # /PS-IGNORE
            "type": "WORK",
            "is_primary": False,
        }
        response = self.importer_client.post(self.importer_url, data=data)
        assert response.status_code == HTTPStatus.FOUND
        assert (
            self.importer_one_contact.emails.get(is_primary=True).email
            == "test@example.com"  # /PS-IGNORE
        )


class TestUserUpdateEmailView:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, importer_one_contact, exporter_client, exporter_one_contact):
        self.importer_email = add_user_email(importer_one_contact, "test_importer_email")
        self.exporter_email = add_user_email(exporter_one_contact, "test_exporter_email")

        self.importer_url = reverse(
            "user-email-edit",
            kwargs={"user_pk": importer_one_contact.pk, "email_pk": self.importer_email.pk},
        )
        self.exporter_url = reverse(
            "user-email-edit",
            kwargs={"user_pk": exporter_one_contact.pk, "email_pk": self.exporter_email.pk},
        )

        self.importer_client = importer_client
        self.exporter_client = exporter_client

    def test_permission(self):
        response = self.importer_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.OK


class TestUserDeleteEmailView:
    @pytest.fixture(autouse=True)
    def setup(self, importer_client, importer_one_contact, exporter_client, exporter_one_contact):
        self.importer_one_contact = importer_one_contact
        self.importer_email = add_user_email(importer_one_contact, "test_importer_email")
        self.exporter_email = add_user_email(exporter_one_contact, "test_exporter_email")

        self.importer_url = reverse(
            "user-email-delete",
            kwargs={"user_pk": importer_one_contact.pk, "email_pk": self.importer_email.pk},
        )
        self.exporter_url = reverse(
            "user-email-delete",
            kwargs={"user_pk": exporter_one_contact.pk, "email_pk": self.exporter_email.pk},
        )

        self.importer_client = importer_client
        self.exporter_client = exporter_client

    def test_permission(self):
        response = self.importer_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.importer_client.post(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.exporter_url)
        assert response.status_code == HTTPStatus.FOUND

    def test_delete_email(self):
        assert self.importer_one_contact.emails.all().count() == 2
        response = self.importer_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FOUND
        assert get_messages_from_response(response) == []
        assert self.importer_one_contact.emails.all().count() == 1

    def test_delete_email_delete_primary_error(self):
        assert self.importer_one_contact.emails.all().count() == 2
        url = reverse(
            "user-email-delete",
            kwargs={
                "user_pk": self.importer_one_contact.pk,
                "email_pk": self.importer_one_contact.emails.get(is_primary=True).pk,
            },
        )

        response = self.importer_client.post(url)
        assert response.status_code == HTTPStatus.FOUND
        assert get_messages_from_response(response) == [
            "Unable to delete Primary email address. Please set another email address as primary before deleting."
        ]
        assert self.importer_one_contact.emails.all().count() == 2

    def test_delete_login_email_error(self):
        login_email = self.importer_one_contact.emails.get(email=self.importer_one_contact.email)
        login_email.is_primary = False
        login_email.save()

        url = reverse(
            "user-email-delete",
            kwargs={"user_pk": self.importer_one_contact.pk, "email_pk": login_email.pk},
        )

        assert self.importer_one_contact.emails.all().count() == 2

        response = self.importer_client.post(url)
        assert response.status_code == HTTPStatus.FOUND
        assert get_messages_from_response(response) == [
            "Unable to delete email address used for account login."
        ]
        assert self.importer_one_contact.emails.all().count() == 2


class TestUsersListView(AuthTestCase):
    url = reverse("users-list")
    redirect_url = f"{LOGIN_URL}?next={url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.context_data["page_title"] == "Maintain Web User Accounts"

    def test_post_action_anonymous_access_redirects(self):
        response = self.anonymous_client.post(self.url, {"action": "archive"})
        assert response.status_code == HTTPStatus.FOUND

    def test_post_action_forbidden_access(self):
        response = self.importer_client.post(self.url, {"action": "archive"})
        assert response.status_code == 403


class TestUserDetailView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("user-details", kwargs={"user_pk": self.importer_user.pk})
        self.redirect_url = f"{LOGIN_URL}?next={self.url}"

    def test_anonymous_access_redirects(self):
        response = self.anonymous_client.get(self.url)
        assert response.status_code == HTTPStatus.FOUND
        assertRedirects(response, self.redirect_url)

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post_not_allowed_for_authorized_user(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


class TestReactivateUserView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("user-reactivate", kwargs={"user_pk": self.importer_user.pk})

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200
        assert (
            response.context_data["page_title"]
            == "Reactivate I1_main_contact_first_name I1_main_contact_last_name's account"
        )

    @pytest.mark.parametrize(
        "send_email",
        (True, False),
    )
    def test_reactivate_user(self, send_email):
        self.importer_user.is_active = False
        self.importer_user.save()
        response = self.ilb_admin_client.post(
            self.url,
            {"subject": "hello", "body": "dd", "send_email": send_email},
        )
        assert response.status_code == HTTPStatus.FOUND

        self.importer_user.refresh_from_db()
        assert self.importer_user.is_active
        if send_email:
            check_gov_notify_email_was_sent(
                1,
                [self.importer_user.email],
                EmailTypes.CASE_EMAIL,
                {"icms_url": get_exporter_site_domain(), "service_name": SiteName.EXPORTER.label},
                exp_subject="hello",
                exp_in_body="dd",
            )
        else:
            check_gov_notify_email_was_sent(0, [], EmailTypes.CASE_EMAIL, {})


class TestDeactivateUserView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.url = reverse("user-deactivate", kwargs={"user_pk": self.importer_user.pk})

    def test_forbidden_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_page_title(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == 200
        assert (
            response.context_data["page_title"]
            == "Deactivate I1_main_contact_first_name I1_main_contact_last_name's account"
        )

    @pytest.mark.parametrize(
        "send_email",
        (True, False),
    )
    def test_deactivate_user(self, send_email):
        assert self.importer_user.is_active
        response = self.ilb_admin_client.post(
            self.url,
            {"subject": "hello", "body": "dd", "send_email": send_email},
        )
        assert response.status_code == HTTPStatus.FOUND

        self.importer_user.refresh_from_db()
        assert not self.importer_user.is_active
        if send_email:
            check_gov_notify_email_was_sent(
                1,
                [self.importer_user.email],
                EmailTypes.CASE_EMAIL,
                {"icms_url": get_exporter_site_domain(), "service_name": SiteName.EXPORTER.label},
                exp_subject="hello",
                exp_in_body="dd",
            )
        else:
            check_gov_notify_email_was_sent(0, [], EmailTypes.CASE_EMAIL, {})


def add_user_email(
    user: User, email_prefix: str, portal_notifications: bool = True, is_primary: bool = False
) -> Email:
    return Email.objects.create(
        user=user,
        email=f"{email_prefix}@example.com",  # /PS-IGNORE
        type=Email.WORK,
        portal_notifications=portal_notifications,
        is_primary=is_primary,
    )


def add_user_phone(user: User, phone: str, _type=PhoneNumber.MOBILE) -> PhoneNumber:
    return PhoneNumber.objects.create(user=user, phone=phone, type=_type)


class TestNewUserWelcomeView:
    def test_importer(self, importer_client):
        url = reverse("user-welcome")
        response = importer_client.get(url)

        assertContains(response, "Welcome to Apply for an import licence")
        assertContains(response, "to start importing products")

    def test_exporter(self, exporter_client):
        url = reverse("user-welcome")
        response = exporter_client.get(url)

        assertContains(response, "Welcome to Apply for an export certificate")
        assertContains(response, "to start exporting products")


class TestClearNewUserWelcomeView:
    def test_importer(self, importer_one_contact, importer_client):
        importer_one_contact.show_welcome_message = True
        importer_one_contact.save()

        url = reverse("user-welcome-clear")
        response = importer_client.post(url)
        assertRedirects(response, reverse("workbasket"))

        importer_one_contact.refresh_from_db()
        assert not importer_one_contact.show_welcome_message

    def test_exporter(self, exporter_one_contact, exporter_client):
        exporter_one_contact.show_welcome_message = True
        exporter_one_contact.save()

        url = reverse("user-welcome-clear")
        response = exporter_client.post(url)
        assertRedirects(response, reverse("workbasket"))

        exporter_one_contact.refresh_from_db()
        assert not exporter_one_contact.show_welcome_message
