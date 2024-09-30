import datetime as dt
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.utils.timezone import make_aware
from freezegun import freeze_time

from web.auth.backends import ICMSGovUKOneLoginBackend, ICMSStaffSSOBackend
from web.one_login.types import UserInfo
from web.sites import SiteName

# NOTE: Copied tests from here:
# https://github.com/uktrade/django-staff-sso-client/blob/master/tests/test_backends.py
# We want the same functionality just with extra logic for ICMS.


@pytest.fixture()
def caseworker_rf(db, rf):
    rf.site = Site.objects.get(name=SiteName.CASEWORKER)
    return rf


@pytest.fixture()
def exporter_rf(db, rf):
    rf.site = Site.objects.get(name=SiteName.EXPORTER)
    return rf


@pytest.fixture()
def importer_rf(db, rf):
    rf.site = Site.objects.get(name=SiteName.IMPORTER)
    return rf


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client")
@mock.patch("authbroker_client.backends.get_profile")
@mock.patch("authbroker_client.backends.has_valid_token")
def test_user_valid_user_create(
    mocked_has_valid_token, mocked_get_profile, mocked_get_client, caseworker_rf
):
    mocked_has_valid_token.return_value = True
    mocked_get_profile.return_value = {
        "email": "user@test.com",  # /PS-IGNORE
        "first_name": "Testo",
        "last_name": "Useri",
        "email_user_id": "an-email_user_id@id.test.com",  # /PS-IGNORE
    }

    user = ICMSStaffSSOBackend().authenticate(request=caseworker_rf)
    assert user is not None

    assert user.first_name == "Testo"
    assert user.last_name == "Useri"
    assert user.email == "user@test.com"  # /PS-IGNORE
    assert user.username == "an-email_user_id@id.test.com"  # /PS-IGNORE
    assert user.has_usable_password() is False
    assert mocked_get_client.called is True
    assert mocked_get_client.call_args == mock.call(caseworker_rf)
    assert mocked_get_profile.call_args == mock.call(mocked_get_client())

    assert user.emails.first().email == "user@test.com"  # /PS-IGNORE


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client", mock.Mock())
@mock.patch("authbroker_client.backends.get_profile")
@mock.patch("authbroker_client.backends.has_valid_token")
def test_user_valid_user_not_create(mocked_has_valid_token, mocked_get_profile, caseworker_rf):
    User = get_user_model()
    user = User(
        username="an-email_user_id@id.test.com",  # /PS-IGNORE
        email="user@test.com",  # /PS-IGNORE
        first_name="Testo",
        last_name="Useri",
    )
    user.set_password("password")
    user.save()
    mocked_has_valid_token.return_value = True
    mocked_get_profile.return_value = {
        "email_user_id": "an-email_user_id@id.test.com",  # /PS-IGNORE
        "email": "user@test.com",  # /PS-IGNORE
        "first_name": "Testo",
        "last_name": "Useri",
    }

    user = ICMSStaffSSOBackend().authenticate(request=caseworker_rf)
    assert user is not None

    assert user.first_name == "Testo"
    assert user.last_name == "Useri"
    assert user.email == "user@test.com"  # /PS-IGNORE
    assert user.has_usable_password() is True


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client", mock.Mock())
@mock.patch("authbroker_client.backends.get_profile")
@mock.patch("authbroker_client.backends.has_valid_token")
def test_user_valid_legacy_user_not_create(
    mocked_has_valid_token, mocked_get_profile, caseworker_rf
):
    User = get_user_model()
    user = User(
        username="user@test.com",  # /PS-IGNORE
        email="user@test.com",  # /PS-IGNORE
        first_name="Testo",
        last_name="Useri",
        icms_v1_user=True,
    )
    user.save()

    mocked_has_valid_token.return_value = True
    mocked_get_profile.return_value = {
        "email_user_id": "an-email_user_id@id.test.com",  # /PS-IGNORE
        "email": "user@test.com",  # /PS-IGNORE
        "first_name": "Testo",
        "last_name": "Useri",
    }

    user = ICMSStaffSSOBackend().authenticate(request=caseworker_rf)
    assert user is not None

    # Username has been migrated to email_user_id value
    assert user.username == "an-email_user_id@id.test.com"  # /PS-IGNORE
    assert user.first_name == "Testo"
    assert user.last_name == "Useri"
    assert user.email == "user@test.com"  # /PS-IGNORE
    assert user.has_usable_password() is False
    assert user.emails.first().email == "user@test.com"  # /PS-IGNORE
    assert user.importer_last_login is None
    assert user.exporter_last_login is None


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client")
@mock.patch("authbroker_client.backends.get_profile")
@mock.patch("authbroker_client.backends.has_valid_token")
def test_user_valid_does_not_authenticate_on_invalid_site(
    mocked_has_valid_token, mocked_get_profile, mocked_get_client, importer_rf, exporter_rf
):
    mocked_has_valid_token.return_value = True
    mocked_get_profile.return_value = {
        "email": "user@test.com",  # /PS-IGNORE
        "first_name": "Testo",
        "last_name": "Useri",
        "email_user_id": "an-email_user_id@id.test.com",  # /PS-IGNORE
    }

    user = ICMSStaffSSOBackend().authenticate(request=importer_rf)
    assert user is None
    assert not mocked_get_client.called
    assert not mocked_get_profile.called

    user = ICMSStaffSSOBackend().authenticate(request=exporter_rf)
    assert user is None
    assert not mocked_get_client.called
    assert not mocked_get_profile.called


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client", mock.Mock())
@mock.patch("authbroker_client.backends.get_profile")
@mock.patch("authbroker_client.backends.has_valid_token")
def test_user_inactive(mocked_has_valid_token, mocked_get_profile, caseworker_rf):
    User = get_user_model()
    user = User(
        username="an-email_user_id@id.test.com",  # /PS-IGNORE
        email="user@test.com",  # /PS-IGNORE
        first_name="Testo",
        last_name="Useri",
        is_active=False,
    )
    user.set_password("password")
    user.save()
    mocked_has_valid_token.return_value = True
    mocked_get_profile.return_value = {
        "email_user_id": "an-email_user_id@id.test.com",  # /PS-IGNORE
        "email": "user@test.com",  # /PS-IGNORE
        "first_name": "Testo",
        "last_name": "Useri",
    }
    user = ICMSStaffSSOBackend().authenticate(request=caseworker_rf)

    # Although the above user has a valid sso token they are inactive so do not authenticate.
    assert user is None


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client", mock.Mock())
@mock.patch("authbroker_client.backends.get_profile", mock.Mock())
@mock.patch("authbroker_client.backends.has_valid_token")
def test_invalid_user(mocked_has_valid_token, caseworker_rf):
    mocked_has_valid_token.return_value = False
    assert ICMSStaffSSOBackend().authenticate(request=caseworker_rf) is None


@pytest.mark.django_db
def test_get_user_user_exists():
    User = get_user_model()
    user = User(
        username="an-email_user_id@id.test.com",  # /PS-IGNORE
        email="user@test.com",  # /PS-IGNORE
        first_name="Testo",
        last_name="Useri",
    )
    user.save()
    assert ICMSStaffSSOBackend().get_user(user.pk) == user


@pytest.mark.django_db
def test_get_user_user_doesnt_exist():
    assert ICMSStaffSSOBackend().get_user(99999) is None


class TestICMSGovUKOneLoginBackend:
    @freeze_time("2024-01-01 12:00:00")
    @mock.patch.multiple(
        "web.one_login.backends",
        get_client=mock.DEFAULT,
        has_valid_token=mock.DEFAULT,
        get_userinfo=mock.DEFAULT,
        autospec=True,
    )
    @mock.patch("web.auth.backends.send_new_user_welcome_email", autospec=True)
    def test_user_valid_user_create(
        self, mock_send_new_user_welcome_email, db, exporter_rf, **mocks
    ):
        mocks["has_valid_token"].return_value = True
        mocks["get_userinfo"].return_value = UserInfo(
            sub="some-unique-key", email="user@test.com", email_verified=True  # /PS-IGNORE
        )

        user = ICMSGovUKOneLoginBackend().authenticate(exporter_rf)
        assert user is not None
        assert user.email == "user@test.com"  # /PS-IGNORE
        assert user.username == "some-unique-key"
        assert user.has_usable_password() is False
        assert user.emails.first().email == "user@test.com"  # /PS-IGNORE
        assert user.importer_last_login is None
        assert user.exporter_last_login == make_aware(dt.datetime(2024, 1, 1, 12, 0, 0))
        assert mock_send_new_user_welcome_email.call_args == mock.call(user, exporter_rf.site)

    @freeze_time("2024-01-01 12:00:00")
    @mock.patch.multiple(
        "web.one_login.backends",
        get_client=mock.DEFAULT,
        has_valid_token=mock.DEFAULT,
        get_userinfo=mock.DEFAULT,
        autospec=True,
    )
    @mock.patch("web.auth.backends.send_new_user_welcome_email", autospec=True)
    def test_user_valid_legacy_user_not_create(
        self, mock_send_new_user_welcome_email, db, importer_rf, **mocks
    ):
        User = get_user_model()
        user = User(
            username="user@test.com",  # /PS-IGNORE
            email="user@test.com",  # /PS-IGNORE
            first_name="Test",
            last_name="User",
            icms_v1_user=True,
            importer_last_login=make_aware(dt.datetime(2020, 12, 1, 9, 1, 0)),
        )
        user.set_password("password")
        user.save()

        mocks["has_valid_token"].return_value = True
        mocks["get_userinfo"].return_value = UserInfo(
            sub="some-unique-key", email="user@test.com", email_verified=True  # /PS-IGNORE
        )

        user = ICMSGovUKOneLoginBackend().authenticate(request=importer_rf)
        assert user is not None

        # Username has been migrated to sub value
        assert user.username == "some-unique-key"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.email == "user@test.com"  # /PS-IGNORE
        assert user.has_usable_password() is False
        assert user.emails.first().email == "user@test.com"  # /PS-IGNORE
        assert user.importer_last_login == make_aware(dt.datetime(2024, 1, 1, 12, 0, 0))
        assert user.exporter_last_login is None
        assert not mock_send_new_user_welcome_email.called

    @freeze_time("2024-01-01 12:00:00")
    @mock.patch.multiple(
        "web.one_login.backends",
        get_client=mock.DEFAULT,
        has_valid_token=mock.DEFAULT,
        get_userinfo=mock.DEFAULT,
        autospec=True,
    )
    @mock.patch("web.auth.backends.send_new_user_welcome_email", autospec=True)
    def test_user_valid_legacy_user_not_create_case_insensitive(
        self, mock_send_new_user_welcome_email, db, importer_rf, **mocks
    ):
        """Has a user unable to log in and migrate their V1 account as their email contained
        a combination of upper and lower case letters."""

        User = get_user_model()
        user = User(
            username="uSeR@TeSt.CoM",  # /PS-IGNORE
            email="uSeR@TeSt.CoM",  # /PS-IGNORE
            first_name="Test",
            last_name="User",
            icms_v1_user=True,
            importer_last_login=make_aware(dt.datetime(2020, 12, 1, 9, 1, 0)),
        )
        user.set_password("password")
        user.save()

        mocks["has_valid_token"].return_value = True
        mocks["get_userinfo"].return_value = UserInfo(
            sub="some-unique-key", email="user@test.com", email_verified=True  # /PS-IGNORE
        )

        user = ICMSGovUKOneLoginBackend().authenticate(request=importer_rf)
        assert user is not None

        # Username has been migrated to sub value
        assert user.username == "some-unique-key"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        # Email has been fixed (no longer upper case)
        assert user.email == "user@test.com"  # /PS-IGNORE
        assert user.has_usable_password() is False
        assert user.emails.first().email == "user@test.com"  # /PS-IGNORE
        assert user.importer_last_login == make_aware(dt.datetime(2024, 1, 1, 12, 0, 0))
        assert user.exporter_last_login is None
        assert not mock_send_new_user_welcome_email.called

    @freeze_time("2024-01-01 12:00:00")
    @mock.patch.multiple(
        "web.one_login.backends",
        get_client=mock.DEFAULT,
        has_valid_token=mock.DEFAULT,
        get_userinfo=mock.DEFAULT,
        autospec=True,
    )
    @mock.patch("web.auth.backends.send_new_user_welcome_email", autospec=True)
    def test_user_valid_does_not_authenticate_on_invalid_site(
        self, mock_send_new_user_welcome_email, db, caseworker_rf, **mocks
    ):
        mocks["has_valid_token"].return_value = True
        mocks["get_userinfo"].return_value = UserInfo(
            sub="some-unique-key", email="user@test.com", email_verified=True  # /PS-IGNORE
        )

        user = ICMSGovUKOneLoginBackend().authenticate(caseworker_rf)
        assert user is None
        assert not mock_send_new_user_welcome_email.called
