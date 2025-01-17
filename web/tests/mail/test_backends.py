from unittest import mock

from django.contrib.sites.models import Site
from django.test import override_settings

from web.mail.constants import EmailTypes
from web.mail.emails import send_new_user_welcome_email
from web.models import Email, EmailTemplate
from web.sites import SiteName


@override_settings(EMAIL_BACKEND="web.mail.backends.GovNotifyEmailBackend")
@mock.patch("web.mail.backends.send_email", autospec=True)
def test_verify_email_is_sent(mock_send_email, importer_one_contact, db):
    # setup
    email = Email.objects.create(
        email="test-unverified-email@example.com",  # /PS-IGNORE
        type=Email.HOME,
        portal_notifications=True,
        is_primary=False,
        is_verified=False,
        user=importer_one_contact,
    )
    importer_one_contact.email = email.email
    importer_one_contact.save()

    site = Site.objects.get(name=SiteName.IMPORTER)

    assert email.verified_reminder_count == 0

    # test
    send_new_user_welcome_email(importer_one_contact, site)

    # assert
    email.refresh_from_db()
    assert email.verified_reminder_count == 1

    assert mock_send_email.apply_async.call_count == 2

    expected_calls = [
        mock.call(
            args=[
                EmailTemplate.objects.get(
                    name=EmailTypes.EMAIL_VERIFICATION
                ).gov_notify_template_id,
                # The personalisation of this email is tested elsewhere
                mock.ANY,
                importer_one_contact.email,
            ]
        ),
        mock.call(
            args=[
                EmailTemplate.objects.get(name=EmailTypes.NEW_USER_WELCOME).gov_notify_template_id,
                # The personalisation of this email is tested elsewhere
                mock.ANY,
                importer_one_contact.email,
            ]
        ),
    ]

    mock_send_email.apply_async.assert_has_calls(expected_calls)
