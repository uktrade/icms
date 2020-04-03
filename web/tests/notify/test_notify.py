from django.core import mail
from django.test import TestCase
from web import models


class TestNotify(TestCase):
    def setUp(self):
        test_user = models.User.objects.create_user(username="tester",
                                                    email="tester@example.com",
                                                    first_name="Tester",
                                                    last_name="Testing")
        test_user.set_password("TestPasS")
        test_user.save()
        models.PersonalEmail(user=test_user,
                             email=test_user.email,
                             portal_notifications=True).save()
        models.PersonalEmail(user=test_user,
                             email='second_email@example.com',
                             portal_notifications=False).save()
        models.AlternativeEmail(user=test_user,
                                email='alternative@example.com',
                                portal_notifications=False).save()
        models.AlternativeEmail(user=test_user,
                                email='second_alternative@example.com',
                                portal_notifications=True).save()
        self.user = test_user

    #  def test_send_email_to_user(self):
    #      email.send_email_to_user.apply(args=('testing', self.user, 'test'))
    #      assert len(mail.outbox) == 1
    #
    #  def test_email_without_subject(self):
    #      email.send_email_to_user.apply(args=(None, self.user, 'test'))
    #      assert len(mail.outbox) == 1
    #
    #  def test_send_to_alternative_email(self):
    #      email.send_email_to_user.apply(args=(None, self.user, 'test'))
    #      m = mail.outbox[0]
    #      assert m.to[1] == 'second_alternative@example.com'
    #
    #  def test_only_sends_to_enabled_emails(self):
    #      email.send_email_to_user.apply(args=(None, self.user, 'test'))
    #      m = mail.outbox[0]
    #      to = m.to
    #      assert len(to) == 2
    #      assert to[0] == 'tester@example.com'
    #      assert to[1] == 'second_alternative@example.com'
    
    #  def test_email_content(self):
    #      email.send_email_to_user.apply(args=('testing', self.user, 'test'))
    #      m = mail.outbox[0]
    #      assert isinstance(m, mail.EmailMultiAlternatives)
    #      assert m.subject == 'testing'
    #      assert m.from_email == 'test@example.com'
