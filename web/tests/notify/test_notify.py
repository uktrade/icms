from django.core import mail
from django.test import TestCase
from django.test.client import RequestFactory

from web import models
from web.notify import notify


class TestNotify(TestCase):
    def setUp(self):
        test_user = models.User.objects.create_user(
            username="tester", email="tester@example.com", first_name="Tester", last_name="Testing"
        )
        test_user.set_password("TestPasS")
        test_user.save()
        models.PersonalEmail(
            user=test_user, email=test_user.email, portal_notifications=True
        ).save()
        models.PersonalEmail(
            user=test_user, email="second_email@example.com", portal_notifications=False
        ).save()
        models.AlternativeEmail(
            user=test_user, email="alternative@example.com", portal_notifications=False
        ).save()
        models.AlternativeEmail(
            user=test_user, email="second_alternative@example.com", portal_notifications=True
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
        assert "tester@example.com" in m.to
        assert "second_alternative@example.com" in m.to
