from datetime import timedelta
from unittest.mock import create_autospec

from django.core import mail
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone

from web import models
from web.domains.case.services import document_pack
from web.forms.fields import JQUERY_DATE_FORMAT
from web.notify import notify, utils
from web.tests.helpers import check_email_was_sent
from web.utils.s3 import get_file_from_s3


class TestNotify(TestCase):
    def setUp(self):
        test_user = models.User.objects.create_user(
            username="tester",
            email="tester@example.com",  # /PS-IGNORE
            first_name="Tester",
            last_name="Testing",
        )
        test_user.set_password("TestPasS")
        test_user.save()
        models.Email(user=test_user, email=test_user.email, portal_notifications=True).save()
        models.Email(
            user=test_user,
            email="second_email@example.com",  # /PS-IGNORE
            portal_notifications=False,
        ).save()
        models.Email(
            user=test_user,
            email="alternative@example.com",  # /PS-IGNORE
            portal_notifications=False,
        ).save()
        models.Email(
            user=test_user,
            email="second_alternative@example.com",  # /PS-IGNORE
            portal_notifications=True,
        ).save()
        self.user = test_user
        self.factory = RequestFactory()

    def test_registration_email(self):
        notify.register(self.user, "TestPasS")
        outbox = mail.outbox
        m = outbox[0]
        assert len(outbox) == 1
        assert len(m.to) == 2
        assert m.subject == "Import Case Management System Account"
        assert "tester@example.com" in m.to  # /PS-IGNORE
        assert "second_alternative@example.com" in m.to  # /PS-IGNORE


def test_send_firearms_authority_expiry_notification(
    ilb_admin_client, importer, constabulary_contact
):
    url = reverse("importer-firearms-create", kwargs={"pk": importer.pk})
    constabulary = models.Constabulary.objects.get(name="Nottingham")

    post_data = {
        "reference": "FA Auth",
        "certificate_type": "FIREARMS",
        "issuing_constabulary": constabulary.pk,
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime(JQUERY_DATE_FORMAT),
        "end_date": (timezone.now() + timedelta(days=30)).strftime(JQUERY_DATE_FORMAT),
        "actquantity_set-TOTAL_FORMS": 0,
        "actquantity_set-INITIAL_FORMS": 0,
        "actquantity_set-MIN_NUM_FORMS": 0,
        "actquantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    post_data = {
        "reference": "Another Auth",
        "certificate_type": "SHOTGUN",
        "issuing_constabulary": constabulary.pk,
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime(JQUERY_DATE_FORMAT),
        "end_date": (timezone.now() + timedelta(days=30)).strftime(JQUERY_DATE_FORMAT),
        "actquantity_set-TOTAL_FORMS": 0,
        "actquantity_set-INITIAL_FORMS": 0,
        "actquantity_set-MIN_NUM_FORMS": 0,
        "actquantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    post_data = {
        "reference": "Not Expiring Auth",
        "certificate_type": "SHOTGUN",
        "issuing_constabulary": constabulary.pk,
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime(JQUERY_DATE_FORMAT),
        "end_date": (timezone.now() + timedelta(days=120)).strftime(JQUERY_DATE_FORMAT),
        "actquantity_set-TOTAL_FORMS": 0,
        "actquantity_set-INITIAL_FORMS": 0,
        "actquantity_set-MIN_NUM_FORMS": 0,
        "actquantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    notify.send_firearms_authority_expiry_notification()

    outbox = mail.outbox
    assert len(outbox) == 1

    m = outbox[0]
    assert m.to == [constabulary_contact.email]  # /PS-IGNORE
    assert m.subject.startswith("Verified Firearms Authorities Expiring")
    assert f"issued by constabulary {constabulary.name} that expire" in m.body
    assert "Firearms Authority references(s)\nAnother Auth, FA Auth\n\n" in m.body
    assert "Not Expiring Auth" not in m.body


def test_no_firearms_authority_expiry_notification(ilb_admin_client, importer):
    url = reverse("importer-firearms-create", kwargs={"pk": importer.pk})
    constabulary = models.Constabulary.objects.first()

    post_data = {
        "reference": "Not Expiring",
        "certificate_type": "FIREARMS",
        "issuing_constabulary": constabulary.pk,
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime(JQUERY_DATE_FORMAT),
        "end_date": (timezone.now() + timedelta(days=120)).strftime(JQUERY_DATE_FORMAT),
        "actquantity_set-TOTAL_FORMS": 0,
        "actquantity_set-INITIAL_FORMS": 0,
        "actquantity_set-MIN_NUM_FORMS": 0,
        "actquantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    notify.send_firearms_authority_expiry_notification()

    outbox = mail.outbox
    assert len(outbox) == 0


def test_send_section_5_authority_expiry_notification(ilb_admin_client, importer):
    url = reverse("importer-section5-create", kwargs={"pk": importer.pk})

    post_data = {
        "reference": "Sec 5",
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime(JQUERY_DATE_FORMAT),
        "end_date": (timezone.now() + timedelta(days=30)).strftime(JQUERY_DATE_FORMAT),
        "clausequantity_set-TOTAL_FORMS": 0,
        "clausequantity_set-INITIAL_FORMS": 0,
        "clausequantity_set-MIN_NUM_FORMS": 0,
        "clausequantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    post_data = {
        "reference": "Another Sec 5",
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime(JQUERY_DATE_FORMAT),
        "end_date": (timezone.now() + timedelta(days=30)).strftime(JQUERY_DATE_FORMAT),
        "clausequantity_set-TOTAL_FORMS": 0,
        "clausequantity_set-INITIAL_FORMS": 0,
        "clausequantity_set-MIN_NUM_FORMS": 0,
        "clausequantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    post_data = {
        "reference": "Not Expiring Sec 5",
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime(JQUERY_DATE_FORMAT),
        "end_date": (timezone.now() + timedelta(days=120)).strftime(JQUERY_DATE_FORMAT),
        "clausequantity_set-TOTAL_FORMS": 0,
        "clausequantity_set-INITIAL_FORMS": 0,
        "clausequantity_set-MIN_NUM_FORMS": 0,
        "clausequantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    notify.send_section_5_expiry_notification()

    outbox = mail.outbox
    assert len(outbox) == 3

    m = outbox[2]
    assert m.to == ["ilb_admin_user@example.com"]  # /PS-IGNORE
    assert m.subject.startswith("Verified Section 5 Authorities Expiring")
    assert "The following 1 importers have one or more verified Section 5 Authorities" in m.body
    assert "references(s) Another Sec 5, Sec 5\n\n" in m.body
    assert "references(s) Another Sec 5, Sec 5\n\n" in m.body
    assert "Not Expiring Sec 5" not in m.body


def test_no_section_5_authority_expiry_notification(ilb_admin_client, importer):
    url = reverse("importer-section5-create", kwargs={"pk": importer.pk})

    post_data = {
        "reference": "Not Expiring Sec 5",
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime(JQUERY_DATE_FORMAT),
        "end_date": (timezone.now() + timedelta(days=120)).strftime(JQUERY_DATE_FORMAT),
        "clausequantity_set-TOTAL_FORMS": 0,
        "clausequantity_set-INITIAL_FORMS": 0,
        "clausequantity_set-MIN_NUM_FORMS": 0,
        "clausequantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    notify.send_section_5_expiry_notification()

    outbox = mail.outbox
    assert len(outbox) == 0


def test_send_constabulary_notification(ilb_admin_user, completed_dfl_app, monkeypatch):
    get_file_from_s3_mock = create_autospec(get_file_from_s3)
    get_file_from_s3_mock.return_value = b"file_content"
    monkeypatch.setattr(utils, "get_file_from_s3", get_file_from_s3_mock)

    app = completed_dfl_app
    doc_pack = document_pack.pack_active_get(app)
    for i, doc_ref in enumerate(doc_pack.document_references.order_by("id")):
        doc_ref.document = models.File.objects.create(
            filename=f"file-{i}",
            content_type="pdf",
            file_size=1,
            path=f"file-path-{i}",
            created_by=ilb_admin_user,
        )
        doc_ref.save()

    notify.send_constabulary_deactivated_firearms_notification(app)

    check_email_was_sent(
        1,
        "constabulary-0-SW@example.com",  # /PS-IGNORE
        "Automatic Notification: Deactivated Firearm Licence Authorised",
        "Attached for information, is a copy of a deactivated firearms import licence",
        [
            ("file-0", b"file_content", "application/octet-stream"),
            ("file-1", b"file_content", "application/octet-stream"),
        ],
    )
