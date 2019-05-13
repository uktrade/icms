from django.core import mail
from django.conf import settings
from django.test import TestCase
from web import email, models
from django.db.utils import IntegrityError
import pytest


@pytest.mark.django_db
class TestEmail(TestCase):
    def test_send_email(self):
        email.send('testing', 'test@example.com', 'test')
        assert len(mail.outbox) == 1

    def test_email_content(self):
        email.send('testing', 'test@example.com', 'test')
        m = mail.outbox[0]
        assert isinstance(m, mail.EmailMultiAlternatives)
        assert m.subject == 'testing'
        assert m.from_email == 'test@example.com'

    def test_email_stored(self):
        mail_count = models.OutboundEmail.objects.filter(
            to_email='test@example.com').count()
        assert mail_count == 0
        email.send('testing', 'test@example.com', 'test')
        mail_count = models.OutboundEmail.objects.filter(
            to_email='test@example.com').count()
        assert mail_count == 1

    def test_message_body_stored_as_attachment(self):
        """
        Test if message body was saved as email attachment
        """
        email.send('testing', 'test@example.com', 'test')
        mail = models.OutboundEmail.objects.filter(
            to_email='test@example.com')[0]
        assert len(mail.attachments.all()) == 1

    def test_status_updated(self):
        email.send('testing', 'test@example.com', 'test')
        mail = models.OutboundEmail.objects.filter(
            to_email='test@example.com')[0]
        assert mail.status == models.OutboundEmail.SENT

    def test_email_without_access_key(self):
        old_key = settings.AWS_ACCESS_KEY_ID
        settings.AWS_ACCESS_KEY_ID = ''
        email.send('testing', 'test@example.com', 'test')
        settings.AWS_ACCESS_KEY_ID = old_key
        assert len(mail.outbox) == 0

    def test_email_without_subject(self):
        email.send(None, 'test@example.com', 'test')

    def test_email_without_to_email(self):
        with pytest.raises(IntegrityError):
            email.send(None, None, 'test')
