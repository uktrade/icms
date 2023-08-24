import pytest
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.core.exceptions import ObjectDoesNotExist

from web.auth.utils import get_legacy_user_by_username, migrate_user


def test_can_check_legacy_user_password(legacy_user):
    assert legacy_user.check_password("TestPassword1!")

    # Test the algorithm gets upgraded
    algorithm, *_ = legacy_user.password.split("$")
    assert algorithm == PBKDF2PasswordHasher.algorithm


def test_get_legacy_user(legacy_user):
    user = get_legacy_user_by_username(legacy_user.username)

    assert user.username == legacy_user.username


def test_get_legacy_user_raises(db):
    with pytest.raises(ObjectDoesNotExist):
        get_legacy_user_by_username("unknown_user")  # /PS-IGNORE


def test_get_v2_user_raises(legacy_user):
    legacy_user.icms_v1_user = False
    legacy_user.save()

    with pytest.raises(ObjectDoesNotExist):
        get_legacy_user_by_username(legacy_user.username)


def test_migrate_user_success(legacy_user, one_login_user):
    migrate_user(one_login_user, legacy_user)

    one_login_user.refresh_from_db()
    legacy_user.refresh_from_db()

    # one_login_user is now inactive
    assert one_login_user.username == "one_login_id_v1_migrated"
    assert not one_login_user.is_active
    assert one_login_user.email == ""
    assert not one_login_user.has_usable_password()

    # Test legacy_user has been updated
    assert legacy_user.username == "one_login_id"
    assert legacy_user.email == "one_login_user@example.com"  # /PS-IGNORE
    assert legacy_user.emails.filter(email="one_login_user@example.com").exists()  # /PS-IGNORE
