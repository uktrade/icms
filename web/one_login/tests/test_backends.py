from unittest import mock

from django.contrib.auth import get_user_model

from web.one_login.backends import OneLoginBackend
from web.one_login.types import UserInfo


@mock.patch.multiple(
    "web.one_login.backends",
    get_client=mock.DEFAULT,
    has_valid_token=mock.DEFAULT,
    get_userinfo=mock.DEFAULT,
    autospec=True,
)
def test_user_valid_user_create(db, rf, **mocks):
    mocks["has_valid_token"].return_value = True
    mocks["get_userinfo"].return_value = UserInfo(
        sub="some-unique-key", email="user@test.com", email_verified=True  # /PS-IGNORE
    )

    user = OneLoginBackend().authenticate(rf)
    assert user is not None
    assert user.email == "user@test.com"  # /PS-IGNORE
    assert user.username == "some-unique-key"
    assert user.has_usable_password() is False


@mock.patch.multiple(
    "web.one_login.backends",
    get_client=mock.DEFAULT,
    has_valid_token=mock.DEFAULT,
    get_userinfo=mock.DEFAULT,
    autospec=True,
)
def test_user_valid_user_not_create(db, rf, **mocks):
    User = get_user_model()
    user = User(
        username="some-unique-key",
        email="user@test.com",  # /PS-IGNORE
        first_name="Test",
        last_name="User",
    )
    user.set_password("password")
    user.save()

    mocks["has_valid_token"].return_value = True
    mocks["get_userinfo"].return_value = UserInfo(
        sub="some-unique-key", email="user@test.com", email_verified=True  # /PS-IGNORE
    )

    user = OneLoginBackend().authenticate(request=rf)
    assert user is not None

    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.email == "user@test.com"  # /PS-IGNORE
    assert user.has_usable_password() is True


@mock.patch.multiple(
    "web.one_login.backends",
    get_client=mock.DEFAULT,
    has_valid_token=mock.DEFAULT,
    get_userinfo=mock.DEFAULT,
    autospec=True,
)
def test_user_inactive(db, rf, **mocks):
    User = get_user_model()
    user = User(
        username="some-unique-key",
        email="user@test.com",  # /PS-IGNORE
        first_name="Test",
        last_name="User",
        is_active=False,
    )
    user.set_password("password")
    user.save()

    mocks["has_valid_token"].return_value = True
    mocks["get_userinfo"].return_value = UserInfo(
        sub="some-unique-key", email="user@test.com", email_verified=True  # /PS-IGNORE
    )

    user = OneLoginBackend().authenticate(request=rf)
    assert user is None


@mock.patch.multiple(
    "web.one_login.backends",
    get_client=mock.DEFAULT,
    has_valid_token=mock.DEFAULT,
    get_userinfo=mock.DEFAULT,
    autospec=True,
)
def test_invalid_user(db, rf, **mocks):
    mocks["has_valid_token"].return_value = False
    assert OneLoginBackend().authenticate(request=rf) is None


def test_get_user_user_exists(db):
    User = get_user_model()
    user = User(
        username="some-unique-key",
        email="user@test.com",  # /PS-IGNORE
        first_name="Test",
        last_name="User",
    )
    user.save()

    assert OneLoginBackend().get_user(user.pk) == user


def test_get_user_user_doesnt_exist(db):
    assert OneLoginBackend().get_user(99999) is None
