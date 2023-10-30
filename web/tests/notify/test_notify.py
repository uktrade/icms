from unittest.mock import create_autospec

from django.core import mail
from django.test import TestCase
from django.test.client import RequestFactory

from web import models
from web.domains.case.services import document_pack
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
