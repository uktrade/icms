#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.core import mail
from django.test import TestCase

from web.domains.user.models import AlternativeEmail, PersonalEmail
from web.notify.notify import utils
from web.tests.domains.user.factory import UserFactory


class TestNotifyUtils(TestCase):
    def test_send_email(self):
        utils.send_email('Subject', 'Message', ['test@example.com'])
        assert len(mail.outbox) == 1

    def test_multipart_email(self):
        utils.send_email('Subject', 'Message',
                         ['test@example.com', '<p>Message</p>'])
        m = mail.outbox[0]
        assert isinstance(m, mail.EmailMultiAlternatives)

    def test_mail_subject(self):
        utils.send_email('Subject', 'Message',
                         ['test@example.com', '<p>Message</p>'])
        m = mail.outbox[0]
        assert m.subject == 'Subject'

    def test_mail_body(self):
        utils.send_email('Subject', 'Message',
                         ['test@example.com', '<p>Message</p>'])
        m = mail.outbox[0]
        assert m.body == 'Message'

    def test_mail_from(self):
        utils.send_email('Subject', 'Message',
                         ['test@example.com', '<p>Message</p>'])
        m = mail.outbox[0]
        assert m.from_email == 'test@example.com'  # in config/settings/test

    def test_mail_to(self):
        utils.send_email(
            'Subject', 'Message',
            ['test@example.com', 'test2@example.com', '<p>Message</p>'])
        m = mail.outbox[0]
        assert m.to[0] == 'test@example.com'
        assert m.to[1] == 'test2@example.com'

    def test_get_notification_emails(self):
        user = UserFactory()
        PersonalEmail(user=user,
                      email='email@example.com',
                      portal_notifications=True).save()
        PersonalEmail(user=user,
                      email='second_email@example.com',
                      portal_notifications=False).save()
        AlternativeEmail(user=user,
                         email='alternative@example.com',
                         portal_notifications=False).save()
        AlternativeEmail(user=user,
                         email='second_alternative@example.com',
                         portal_notifications=True).save()
        emails = utils.get_notification_emails(user)
        assert len(emails) == 2
        assert emails[0] == 'email@example.com'
        assert emails[1] == 'second_alternative@example.com'
