import pytest

from web.models import AlternativeEmail, PersonalEmail
from web.notify.notify import utils
from web.tests.domains.user.factory import UserFactory


@pytest.mark.django_db
def test_get_notification_emails():
    user = UserFactory()
    PersonalEmail(
        user=user, email="email@example.com", portal_notifications=True  # /PS-IGNORE
    ).save()
    PersonalEmail(
        user=user, email="second_email@example.com", portal_notifications=False  # /PS-IGNORE
    ).save()
    AlternativeEmail(
        user=user, email="alternative@example.com", portal_notifications=False  # /PS-IGNORE
    ).save()
    AlternativeEmail(
        user=user,
        email="second_alternative@example.com",  # /PS-IGNORE
        portal_notifications=True,
    ).save()
    emails = utils.get_notification_emails(user)
    assert len(emails) == 2
    assert emails[0] == "email@example.com"  # /PS-IGNORE
    assert emails[1] == "second_alternative@example.com"  # /PS-IGNORE
