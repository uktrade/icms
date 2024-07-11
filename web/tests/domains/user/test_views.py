from http import HTTPStatus
from typing import Any

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.forms.fields import JQUERY_DATE_FORMAT
from web.mail.constants import EmailTypes
from web.models import Email, PhoneNumber, User
from web.one_login.constants import ONE_LOGIN_UNSET_NAME
from web.sites import get_exporter_site_domain
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.helpers import check_gov_notify_email_was_sent


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

        self.importer_url = reverse("new-user-edit", kwargs={"user_pk": importer_one_contact.pk})
        self.exporter_url = reverse("new-user-edit", kwargs={"user_pk": exporter_one_contact.pk})

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
                {"icms_url": get_exporter_site_domain()},
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
                {"icms_url": get_exporter_site_domain()},
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


def add_user_phone(user: User, phone: str, type=PhoneNumber.MOBILE) -> PhoneNumber:
    return PhoneNumber.objects.create(user=user, phone=phone, type=type)
