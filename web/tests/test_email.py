from django.core import mail
from django.test import TestCase
from web import models
from web.notify import email


class TestEmail(TestCase):
    def setUp(self):
        test_user = models.User.objects.create_user(
            username="tester",
            email="tester@example.com",
            first_name="Tester",
            last_name="Testing")
        test_user.set_password("TestPasS")
        test_user.save()
        models.PersonalEmail(
            user=test_user, email=test_user.email,
            portal_notifications=True).save()
        return test_user

    def user(self):
        return models.User.objects.get(username="tester")

    def test_send_email(self):
        email.send('testing', self.user(), 'test')
        assert len(mail.outbox) == 1

    def test_email_without_subject(self):
        email.send(None, self.user(), 'test')
        assert len(mail.outbox) == 1

    def test_email_content(self):
        email.send('testing', self.user(), 'test')
        m = mail.outbox[0]
        assert isinstance(m, mail.EmailMultiAlternatives)
        assert m.subject == 'testing'
        assert m.from_email == 'test@example.com'
