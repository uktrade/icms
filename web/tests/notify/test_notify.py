from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone

from web import models
from web.notify import notify


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
        models.PersonalEmail(
            user=test_user, email=test_user.email, portal_notifications=True
        ).save()
        models.PersonalEmail(
            user=test_user,
            email="second_email@example.com",  # /PS-IGNORE
            portal_notifications=False,
        ).save()
        models.AlternativeEmail(
            user=test_user,
            email="alternative@example.com",  # /PS-IGNORE
            portal_notifications=False,
        ).save()
        models.AlternativeEmail(
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


def test_send_firearms_authority_expiry_notification(ilb_admin_client, importer):
    url = reverse("importer-firearms-create", kwargs={"pk": importer.pk})
    constabulary = models.Constabulary.objects.first()

    post_data = {
        "reference": "FA Auth",
        "certificate_type": "FIREARMS",
        "issuing_constabulary": constabulary.pk,
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime("%d-%b-%Y"),
        "end_date": (timezone.now() + timedelta(days=30)).strftime("%d-%b-%Y"),
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
        "start_date": timezone.now().strftime("%d-%b-%Y"),
        "end_date": (timezone.now() + timedelta(days=30)).strftime("%d-%b-%Y"),
        "actquantity_set-TOTAL_FORMS": 0,
        "actquantity_set-INITIAL_FORMS": 0,
        "actquantity_set-MIN_NUM_FORMS": 0,
        "actquantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    notify.send_firearms_authority_expiry_notification()

    outbox = mail.outbox
    assert len(outbox) == 2

    m = outbox[1]
    assert m.to == ["ilb_admin_user@email.com"]  # /PS-IGNORE
    assert m.subject.startswith("Verified Firearms Authorities Expiring")
    assert f"issued by constabulary {constabulary.name} that expire" in m.body
    assert "Firearms Authority references(s)\nAnother Auth, FA Auth\n\n" in m.body


def test_send_section_5_authority_expiry_notification(ilb_admin_client, importer):
    url = reverse("importer-section5-create", kwargs={"pk": importer.pk})

    post_data = {
        "reference": "Sec 5",
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime("%d-%b-%Y"),
        "end_date": (timezone.now() + timedelta(days=30)).strftime("%d-%b-%Y"),
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
        "start_date": timezone.now().strftime("%d-%b-%Y"),
        "end_date": (timezone.now() + timedelta(days=30)).strftime("%d-%b-%Y"),
        "clausequantity_set-TOTAL_FORMS": 0,
        "clausequantity_set-INITIAL_FORMS": 0,
        "clausequantity_set-MIN_NUM_FORMS": 0,
        "clausequantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    notify.send_section_5_expiry_notification()

    outbox = mail.outbox
    assert len(outbox) == 2

    m = outbox[1]
    assert m.to == ["ilb_admin_user@email.com"]  # /PS-IGNORE
    assert m.subject.startswith("Verified Section 5 Authorities Expiring")
    assert "The following 1 importers have one or more verified Section 5 Authorities" in m.body
    assert "references(s) Another Sec 5, Sec 5\n\n" in m.body


def test_firearms_authority_archived_notification(ilb_admin_client, importer):
    url = reverse("importer-firearms-create", kwargs={"pk": importer.pk})
    constabulary = models.Constabulary.objects.first()

    post_data = {
        "reference": "FA Auth",
        "certificate_type": "FIREARMS",
        "issuing_constabulary": constabulary.pk,
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime("%d-%b-%Y"),
        "end_date": (timezone.now() + timedelta(days=30)).strftime("%d-%b-%Y"),
        "actquantity_set-TOTAL_FORMS": 0,
        "actquantity_set-INITIAL_FORMS": 0,
        "actquantity_set-MIN_NUM_FORMS": 0,
        "actquantity_set-MAX_NUM_FORMS": 1000,
    }

    ilb_admin_client.post(url, post_data)

    fa_auth = importer.firearms_authorities.get(reference="FA Auth")
    url = reverse("importer-firearms-archive", kwargs={"pk": fa_auth.pk})
    post_data = {"archive_reason": ["REVOKED", "OTHER"], "other_archive_reason": "test reason"}
    resp = ilb_admin_client.post(url, post_data)
    assert resp.status_code == 302

    outbox = mail.outbox
    assert len(outbox) == 2

    m = outbox[1]
    assert m.to == ["ilb_admin_user@email.com"]  # /PS-IGNORE
    assert m.subject.startswith(
        f"Importer {importer.id} Verified Firearms Authority FA Auth Archived"
    )
    assert (
        "been archived for the following reason(s):\n\nRevoked\n\nOther: test reason\n\n" in m.body
    )


def test_section_5_authority_archived_notification(ilb_admin_client, importer):
    url = reverse("importer-section5-create", kwargs={"pk": importer.pk})

    post_data = {
        "reference": "Sec 5",
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime("%d-%b-%Y"),
        "end_date": (timezone.now() + timedelta(days=30)).strftime("%d-%b-%Y"),
        "clausequantity_set-TOTAL_FORMS": 0,
        "clausequantity_set-INITIAL_FORMS": 0,
        "clausequantity_set-MIN_NUM_FORMS": 0,
        "clausequantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    sec5 = importer.section5_authorities.get(reference="Sec 5")
    url = reverse("importer-section5-archive", kwargs={"pk": sec5.pk})
    post_data = {"archive_reason": ["WITHDRAWN", "REFUSED"], "other_archive_reason": ""}
    resp = ilb_admin_client.post(url, post_data)

    assert resp.status_code == 302

    outbox = mail.outbox
    assert len(outbox) == 2

    m = outbox[1]
    assert m.to == ["ilb_admin_user@email.com"]  # /PS-IGNORE
    assert m.subject.startswith(
        f"Importer {importer.id} Verified Section 5 Authority Sec 5 Archived"
    )
    assert "been archived for the following reason(s):\n\nWithdrawn\n\nRefused\n\n" in m.body


def test_firearms_authority_archived_notification_fail(ilb_admin_client, importer):
    url = reverse("importer-firearms-create", kwargs={"pk": importer.pk})
    constabulary = models.Constabulary.objects.first()

    post_data = {
        "reference": "FA Auth",
        "certificate_type": "FIREARMS",
        "issuing_constabulary": constabulary.pk,
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime("%d-%b-%Y"),
        "end_date": (timezone.now() + timedelta(days=30)).strftime("%d-%b-%Y"),
        "actquantity_set-TOTAL_FORMS": 0,
        "actquantity_set-INITIAL_FORMS": 0,
        "actquantity_set-MIN_NUM_FORMS": 0,
        "actquantity_set-MAX_NUM_FORMS": 1000,
    }

    ilb_admin_client.post(url, post_data)

    fa_auth = importer.firearms_authorities.get(reference="FA Auth")
    url = reverse("importer-firearms-archive", kwargs={"pk": fa_auth.pk})
    post_data = {"archive_reason": ["REVOKED", "OTHER"], "other_archive_reason": ""}
    resp = ilb_admin_client.post(url, post_data)
    assert resp.status_code == 200

    outbox = mail.outbox
    assert len(outbox) == 0


def test_section_5_authority_archived_notification_fail(ilb_admin_client, importer):
    url = reverse("importer-section5-create", kwargs={"pk": importer.pk})

    post_data = {
        "reference": "Sec 5",
        "postcode": "abc",
        "address": "123",
        "start_date": timezone.now().strftime("%d-%b-%Y"),
        "end_date": (timezone.now() + timedelta(days=30)).strftime("%d-%b-%Y"),
        "clausequantity_set-TOTAL_FORMS": 0,
        "clausequantity_set-INITIAL_FORMS": 0,
        "clausequantity_set-MIN_NUM_FORMS": 0,
        "clausequantity_set-MAX_NUM_FORMS": 1000,
    }
    ilb_admin_client.post(url, post_data)

    sec5 = importer.section5_authorities.get(reference="Sec 5")
    url = reverse("importer-section5-archive", kwargs={"pk": sec5.pk})
    post_data = {"archive_reason": ["WITHDRAWN", "OTHER"], "other_archive_reason": ""}
    resp = ilb_admin_client.post(url, post_data)

    assert resp.status_code == 200

    outbox = mail.outbox
    assert len(outbox) == 0
