from datetime import timedelta
from unittest.mock import create_autospec, patch

import pytest
from django.core import mail
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone

from web import models
from web.domains.case.services import document_pack
from web.notify import notify, utils
from web.tests.helpers import (
    CaseURLS,
    add_variation_request_to_app,
    check_email_was_sent,
)
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
    assert len(outbox) == 3

    m = outbox[2]
    assert m.to == ["ilb_admin_user@example.com"]  # /PS-IGNORE
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
    assert len(outbox) == 3

    m = outbox[2]
    assert m.to == ["ilb_admin_user@example.com"]  # /PS-IGNORE
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
    assert len(outbox) == 3

    m = outbox[1]
    assert m.to == ["ilb_admin_user@example.com"]  # /PS-IGNORE
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
    assert len(outbox) == 3

    m = outbox[1]
    assert m.to == ["ilb_admin_user@example.com"]  # /PS-IGNORE
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


def test_send_application_approved_notification(completed_sil_app, importer_one_contact):
    app = completed_sil_app
    notify.send_application_approved_notification(completed_sil_app)

    check_email_was_sent(
        1,
        importer_one_contact.email,
        f"Application reference {app.reference} has been approved by ILB.",
        f"Your application, case reference {app.reference}, has been approved by ILB.",
    )


def test_send_sil_application_approved_email_vr(
    ilb_admin_user, completed_sil_app, importer_one_contact
):
    app = completed_sil_app
    add_variation_request_to_app(
        app, ilb_admin_user, status=models.VariationRequest.Statuses.ACCEPTED
    )
    notify.send_application_approved_notification(completed_sil_app)

    check_email_was_sent(
        1,
        importer_one_contact.email,
        f"Variation on application reference {app.reference} has been approved by ILB.",
        f"The requested variation on case reference {app.reference} has been approved",
    )


def test_send_sil_application_approved_email_licence_extension(
    ilb_admin_user, completed_sil_app, importer_one_contact
):
    app = completed_sil_app
    add_variation_request_to_app(
        app, ilb_admin_user, status=models.VariationRequest.Statuses.ACCEPTED, extension_flag=True
    )
    notify.send_application_approved_notification(completed_sil_app)

    check_email_was_sent(
        1,
        importer_one_contact.email,
        f"Extension to application reference {app.reference} has been approved.",
        f"The requested extension to case reference {app.reference} has been approved.",
    )


def test_send_supplentary_report_notification(completed_sil_app, importer_one_contact):
    app = completed_sil_app
    notify.send_supplementary_report_notification(app)

    check_email_was_sent(
        1,
        importer_one_contact.email,
        f"Firearms supplementary reporting information on application reference {app.reference}",
        "Commission Delegated Regulation (EU) 2019/686 introduced arrangements",
    )


def test_send_constabulary_notification(ilb_admin_user, completed_dfl_app, monkeypatch):
    get_file_from_s3_mock = create_autospec(get_file_from_s3)
    get_file_from_s3_mock.return_value = b"file_content"
    monkeypatch.setattr(utils, "get_file_from_s3", get_file_from_s3_mock)

    app = completed_dfl_app
    doc_pack = document_pack.pack_active_get(app)
    for i, doc_ref in enumerate(doc_pack.document_references.all()):
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


@patch("web.notify.notify.send_constabulary_deactivated_firearms_notification")
@patch("web.notify.notify.send_supplementary_report_notification")
@patch("web.notify.notify.send_application_approved_notification")
def test_send_case_complete_notifications_dfl(
    app_approved_mock, supplementay_report_mock, constabulary_mock, completed_dfl_app
):
    app = completed_dfl_app
    notify.send_case_complete_notifications(app)

    app_approved_mock.assert_called_with(app)
    supplementay_report_mock.assert_called_with(app)
    constabulary_mock.assert_called_with(app.dflapplication)


@patch("web.notify.notify.send_constabulary_deactivated_firearms_notification")
@patch("web.notify.notify.send_supplementary_report_notification")
@patch("web.notify.notify.send_application_approved_notification")
def test_send_case_complete_notifications_sil(
    app_approved_mock, supplementay_report_mock, constabulary_mock, completed_sil_app
):
    app = completed_sil_app
    notify.send_case_complete_notifications(app)

    app_approved_mock.assert_called_with(app)
    supplementay_report_mock.assert_called_with(app)
    constabulary_mock.assert_not_called()


@patch("web.notify.notify.send_constabulary_deactivated_firearms_notification")
@patch("web.notify.notify.send_supplementary_report_notification")
@patch("web.notify.notify.send_application_approved_notification")
def test_send_case_complete_notifications_gmp(
    app_approved_mock, supplementay_report_mock, constabulary_mock, gmp_app_submitted
):
    app = gmp_app_submitted
    notify.send_case_complete_notifications(app)

    app_approved_mock.assert_called_with(app)
    supplementay_report_mock.assert_not_called()
    constabulary_mock.assert_not_called()


def _create_fir(user):
    return models.FurtherInformationRequest.objects.create(
        process_type=models.FurtherInformationRequest.PROCESS_TYPE,
        requested_by=user,
        status=models.FurtherInformationRequest.OPEN,
        request_subject="test subject",
        request_detail="test request detail",
    )


def test_send_fir_access_request(ilb_admin_user, importer_access_request, access_request_user):
    process = importer_access_request
    user = access_request_user

    fir = _create_fir(ilb_admin_user)
    process.further_information_requests.add(fir)

    context = {"subject": "FIR Subject", "body": "FIR Body"}

    attachments = [
        ("file-0", b"file_content"),
        ("file-1", b"file_content"),
    ]

    notify.send_fir_to_contacts(process, fir, context, attachments)

    check_email_was_sent(
        1,
        user.email,
        "FIR Subject",
        "FIR Body",
        # TODO ICMSLST-2061
        # [
        #    ("file-0", b"file_content", "application/octet-stream"),
        #     ("file-1", b"file_content", "application/octet-stream"),
        # ],
    )


def test_send_fir_import_application(
    ilb_admin_client, ilb_admin_user, fa_sil_app_submitted, importer_one_contact
):
    process = fa_sil_app_submitted
    user = importer_one_contact

    ilb_admin_client.post(CaseURLS.take_ownership(process.pk))
    process.refresh_from_db()

    fir = _create_fir(ilb_admin_user)
    process.further_information_requests.add(fir)

    context = {"subject": "FIR Subject", "body": "FIR Body"}

    notify.send_fir_to_contacts(process, fir, context)

    check_email_was_sent(
        1,
        user.email,
        "FIR Subject",
        "FIR Body",
    )


def test_send_fir_export_application(
    ilb_admin_client, ilb_admin_user, gmp_app_submitted, exporter_one_contact
):
    process = gmp_app_submitted
    user = exporter_one_contact

    ilb_admin_client.post(CaseURLS.take_ownership(process.pk, "export"))
    process.refresh_from_db()

    fir = _create_fir(ilb_admin_user)
    process.further_information_requests.add(fir)

    context = {"subject": "FIR Subject", "body": "FIR Body"}

    notify.send_fir_to_contacts(process, fir, context)

    check_email_was_sent(
        1,
        user.email,
        "FIR Subject",
        "FIR Body",
    )


def test_send_fir_error(ilb_admin_user):
    process = _create_fir(ilb_admin_user)
    fir = _create_fir(ilb_admin_user)
    context = {"subject": "FIR Subject", "body": "FIR Body"}

    with pytest.raises(ValueError) as e_info:
        notify.send_fir_to_contacts(process, fir, context)
        assert (
            e_info
            == "Process must be an instance of ImportApplication / ExportApplication / AccessRequest"
        )


@patch("web.notify.notify.send_fir_to_contacts")
def test_send_further_information_request(
    mock_send_fir, monkeypatch, ilb_admin_user, importer_access_request
):
    get_file_from_s3_mock = create_autospec(get_file_from_s3)
    get_file_from_s3_mock.return_value = b"file_content"
    monkeypatch.setattr(utils, "get_file_from_s3", get_file_from_s3_mock)

    process = importer_access_request

    fir = _create_fir(ilb_admin_user)
    process.further_information_requests.add(fir)

    for i in range(2):
        f = models.File.objects.create(
            filename=f"file-{i}",
            content_type="pdf",
            file_size=1,
            path=f"file-path-{i}",
            created_by=ilb_admin_user,
        )
        fir.files.add(f)

    context = {"subject": fir.request_subject, "body": fir.request_detail}

    attachments = [
        ("file-0", b"file_content"),
        ("file-1", b"file_content"),
    ]

    notify.send_further_information_request(process, fir)
    mock_send_fir.assert_called_once_with(process, fir, context, attachments)


@patch("web.notify.notify.send_fir_to_contacts")
def test_send_send_further_information_request_withdrawal(
    mock_send_fir, ilb_admin_user, fa_sil_app_submitted
):
    process = fa_sil_app_submitted
    fir = _create_fir(ilb_admin_user)
    subject = f"Withdrawn - {process.reference} Further Information Request"
    body = "The FIR request has been withdrawn by ILB."

    notify.send_further_information_request_withdrawal(process, fir)
    mock_send_fir.assert_called_once_with(process, fir, {"subject": subject, "body": body})


def test_fir_responded_access_request(ilb_admin_user, importer_access_request):
    process = importer_access_request
    fir = _create_fir(ilb_admin_user)
    subject = f"FIR Response - {process.reference} - {fir.request_subject}"
    notify.further_information_responded(process, fir)

    check_email_was_sent(
        1,
        ilb_admin_user.email,
        subject,
        f"A FIR response has been submitted for access request {process.reference}",
    )


def test_fir_responded_case(ilb_admin_user, fa_sil_app_submitted):
    process = fa_sil_app_submitted
    fir = _create_fir(ilb_admin_user)
    subject = f"FIR Response - {process.reference} - {fir.request_subject}"
    notify.further_information_responded(process, fir)

    check_email_was_sent(
        1,
        ilb_admin_user.email,
        subject,
        f"A FIR response has been submitted for case {process.reference}",
    )
