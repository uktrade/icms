import datetime as dt
from unittest import mock

from django.contrib.sites.models import Site
from django.utils import timezone
from freezegun import freeze_time

from web.domains.user.utils import send_and_create_email_verification
from web.mail.constants import EmailTypes
from web.mail.url_helpers import get_email_verification_url
from web.models import Email, EmailVerification
from web.sites import SiteName, get_importer_site_domain
from web.tests.helpers import check_gov_notify_email_was_sent


def test_send_and_create_email_verification(importer_one_contact):
    email = Email.objects.create(
        email="test_verify@example.com", type=Email.WORK, user=importer_one_contact  # /PS-IGNORE
    )
    site = Site.objects.get(name=SiteName.IMPORTER)

    send_and_create_email_verification(email, site)

    email.refresh_from_db()
    assert email.emailverification_set.count() == 1
    _assert_email_sent(email.emailverification_set.first())


def test_resend_and_create_email_verification(importer_one_contact):
    email = Email.objects.create(
        email="test_verify@example.com", type=Email.WORK, user=importer_one_contact  # /PS-IGNORE
    )
    verification = EmailVerification.objects.create(email=email)

    site = Site.objects.get(name=SiteName.IMPORTER)

    send_and_create_email_verification(email, site)

    email.refresh_from_db()

    assert email.emailverification_set.count() == 1
    assert email.emailverification_set.first() == verification
    _assert_email_sent(verification)


def test_resend_and_create_email_verification_for_expired_email_verification(importer_one_contact):
    email = Email.objects.create(
        email="test_verify@example.com", type=Email.WORK, user=importer_one_contact  # /PS-IGNORE
    )
    older_than_two_weeks = timezone.now() - dt.timedelta(weeks=2, microseconds=1)
    with freeze_time(older_than_two_weeks):
        verification = EmailVerification.objects.create(email=email)

    site = Site.objects.get(name=SiteName.IMPORTER)

    send_and_create_email_verification(email, site)

    latest_verification = email.emailverification_set.last()

    email.refresh_from_db()
    verification.refresh_from_db()

    assert email.emailverification_set.count() == 2
    assert email.emailverification_set.last() != verification
    assert verification.processed is True
    assert latest_verification.processed is False
    _assert_email_sent(latest_verification)


@mock.patch("web.domains.user.utils.send_email_verification_email", autospec=True)
def test_resend_and_create_email_verification_limit_exceeded(
    mock_send_email_verification_email, importer_one_contact
):
    email = Email.objects.create(
        email="test_verify@example.com",  # /PS-IGNORE
        type=Email.WORK,
        user=importer_one_contact,
        is_primary=False,
        is_verified=False,
        portal_notifications=True,
        verified_reminder_count=5,
    )

    site = Site.objects.get(name=SiteName.IMPORTER)
    send_and_create_email_verification(email, site)

    email.refresh_from_db()

    assert email.verified_reminder_count == 0
    assert not email.portal_notifications

    mock_send_email_verification_email.assert_not_called()

    assert email.emailverification_set.count() == 1
    verification = email.emailverification_set.first()
    assert verification.processed


def _assert_email_sent(verification: EmailVerification) -> None:
    check_gov_notify_email_was_sent(
        1,
        ["test_verify@example.com"],  # /PS-IGNORE
        EmailTypes.EMAIL_VERIFICATION,
        {
            "icms_url": get_importer_site_domain(),
            "service_name": SiteName.IMPORTER.label,
            "email_verification_url": get_email_verification_url(
                verification, get_importer_site_domain()
            ),
        },
    )
