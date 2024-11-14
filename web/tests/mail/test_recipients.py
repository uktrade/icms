import pytest
from django.test import override_settings

from web.mail.recipients import (
    get_ilb_case_officers_email_addresses,
    get_organisation_contact_email_addresses,
)


@pytest.mark.django_db
def test_get_ilb_case_officers_email_addresses():
    recipients = get_ilb_case_officers_email_addresses()

    assert sorted(recipient.email_address for recipient in recipients) == sorted(
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
        recipients = get_ilb_case_officers_email_addresses()
        assert [recipient.email_address for recipient in recipients] == [
            "test_user@example.com"  # /PS-IGNORE
        ]


@pytest.mark.django_db
def test_get_importer_organisation_contact_email_addresses(importer, importer_one_contact):
    recipients = get_organisation_contact_email_addresses(importer)
    assert [recipient.email_address for recipient in recipients] == [importer_one_contact.email]
