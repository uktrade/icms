import pytest
from django.test import override_settings

from web.mail.recipients import get_ilb_case_officers_email_addresses


@pytest.mark.django_db
def test_get_ilb_case_officers_email_addresses():
    assert sorted(get_ilb_case_officers_email_addresses()) == sorted(
        [
            "ilb_admin_user@example.com",  # /PS-IGNORE
            "ilb_admin_two@example.com",  # /PS-IGNORE
        ]
    )


@pytest.mark.django_db
def test_get_ilb_case_officers_email_addresses_override_recipients():
    with override_settings(
        APP_ENV="dev", SEND_ALL_EMAILS_TO=["test_user@example.com"]  # /PS-IGNORE
    ):
        assert get_ilb_case_officers_email_addresses() == ["test_user@example.com"]  # /PS-IGNORE
