import pytest

from web.models import AlternativeEmail, PersonalEmail
from web.notify.notify import utils
from web.permissions.perms import ExporterObjectPermissions, ImporterObjectPermissions
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


@pytest.mark.django_db
def test_get_importer_contacts(importer):
    result = utils.get_importer_contacts(importer)
    assert result.count() == 1
    assert result.first().username == "I1_main_contact"


@pytest.mark.django_db
def test_get_importer_contacts_view_permission(importer):
    result = utils.get_importer_contacts(importer, ImporterObjectPermissions.is_contact.codename)
    assert result.count() == 3
    assert list(result.order_by("username").values_list("username", flat=True)) == [
        "I1_main_contact",
        "importer_contact",
        "test_import_user",
    ]


@pytest.mark.django_db
def test_get_exporter_contacts(exporter):
    result = utils.get_exporter_contacts(exporter)
    assert result.count() == 1
    assert result.first().username == "E1_main_contact"


@pytest.mark.django_db
def test_get_exporter_contacts_view_permission(exporter):
    result = utils.get_exporter_contacts(exporter, ExporterObjectPermissions.is_contact.codename)
    assert result.count() == 3
    assert list(result.order_by("username").values_list("username", flat=True)) == [
        "E1_main_contact",
        "exporter_contact",
        "test_export_user",
    ]
