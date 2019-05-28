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

    def test_email_stored(self):
        mail_count = models.OutboundEmail.objects.filter(
            to_email='tester@example.com').count()
        assert mail_count == 0
        email.send('testing', self.user(), 'test')
        mail_count = models.OutboundEmail.objects.filter(
            to_email='tester@example.com').count()
        assert mail_count == 1

    def test_message_body_stored_as_attachment(self):
        """
        Test if message body was saved as email attachment
        """
        email.send('testing', self.user(), 'test')
        mail = models.OutboundEmail.objects.filter(
            to_email='tester@example.com')[0]
        assert len(mail.attachments.all()) == 1

    def test_status_updated(self):
        email.send('testing', self.user(), 'test')
        mail = models.OutboundEmail.objects.filter(
            to_email='tester@example.com')[0]
        assert mail.status == models.OutboundEmail.SENT
