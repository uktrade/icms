from unittest import mock

import pytest
from django.contrib.auth import get_user_model

from web.auth.backends import ICMSStaffSSOBackend

# NOTE: Copied tests from here:
# https://github.com/uktrade/django-staff-sso-client/blob/master/tests/test_backends.py
# We want the same functionality just with extra logic for ICMS.


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client")
@mock.patch("authbroker_client.backends.get_profile")
@mock.patch("authbroker_client.backends.has_valid_token")
def test_user_valid_user_create(mocked_has_valid_token, mocked_get_profile, mocked_get_client, rf):
    mocked_has_valid_token.return_value = True
    mocked_get_profile.return_value = {
        "email": "user@test.com",  # /PS-IGNORE
        "first_name": "Testo",
        "last_name": "Useri",
        "email_user_id": "an-email_user_id@id.test.com",  # /PS-IGNORE
    }

    user = ICMSStaffSSOBackend().authenticate(request=rf)
    assert user is not None

    assert user.first_name == "Testo"
    assert user.last_name == "Useri"
    assert user.email == "user@test.com"  # /PS-IGNORE
    assert user.username == "an-email_user_id@id.test.com"  # /PS-IGNORE
    assert user.has_usable_password() is False
    assert mocked_get_client.called is True
    assert mocked_get_client.call_args == mock.call(rf)
    assert mocked_get_profile.call_args == mock.call(mocked_get_client())

    assert user.emails.first().email == "user@test.com"  # /PS-IGNORE


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client", mock.Mock())
@mock.patch("authbroker_client.backends.get_profile")
@mock.patch("authbroker_client.backends.has_valid_token")
def test_user_valid_user_not_create(mocked_has_valid_token, mocked_get_profile, rf):
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

    user = ICMSStaffSSOBackend().authenticate(request=rf)
    assert user is not None

    assert user.first_name == "Testo"
    assert user.last_name == "Useri"
    assert user.email == "user@test.com"  # /PS-IGNORE
    assert user.has_usable_password() is True


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client", mock.Mock())
@mock.patch("authbroker_client.backends.get_profile")
@mock.patch("authbroker_client.backends.has_valid_token")
def test_user_valid_legacy_user_not_create(mocked_has_valid_token, mocked_get_profile, rf):
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

    user = ICMSStaffSSOBackend().authenticate(request=rf)
    assert user is not None

    # Username has been migrated to email_user_id value
    assert user.username == "an-email_user_id@id.test.com"  # /PS-IGNORE
    assert user.first_name == "Testo"
    assert user.last_name == "Useri"
    assert user.email == "user@test.com"  # /PS-IGNORE
    assert user.has_usable_password() is False
    assert user.emails.first().email == "user@test.com"  # /PS-IGNORE


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client", mock.Mock())
@mock.patch("authbroker_client.backends.get_profile")
@mock.patch("authbroker_client.backends.has_valid_token")
def test_user_inactive(mocked_has_valid_token, mocked_get_profile, rf):
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
    user = ICMSStaffSSOBackend().authenticate(request=rf)

    # Although the above user has a valid sso token they are inactive so do not authenticate.
    assert user is None


@pytest.mark.django_db
@mock.patch("authbroker_client.backends.get_client", mock.Mock())
@mock.patch("authbroker_client.backends.get_profile", mock.Mock())
@mock.patch("authbroker_client.backends.has_valid_token")
def test_invalid_user(mocked_has_valid_token, rf):
    mocked_has_valid_token.return_value = False
    assert ICMSStaffSSOBackend().authenticate(request=rf) is None


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
