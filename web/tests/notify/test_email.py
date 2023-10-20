from django.core import mail
from django.test import TestCase

from web.models import Email, User
from web.notify import email


class TestEmail(TestCase):
    def create_user_emails(self, members=None):
        if not members:
            members = []

        for member in members:
            user = User.objects.get(username=member["username"])

            for m in member.get("email", []):
                Email(user=user, email=m["email"], portal_notifications=m["notify"]).save()

    def setup_user_emails(self):
        # An active import organisation
        self.create_user_emails(
            members=[
                {
                    "username": "I1_main_contact",
                    "email": [
                        {
                            "email": "I1_main_contact_second_email@example.com",  # /PS-IGNORE
                            "notify": True,
                        },
                        {
                            "email": "I1_main_contact_no_notify@example.com",  # /PS-IGNORE
                            "notify": False,
                        },
                        {"email": "I1_main_contact_alt@example.com", "notify": True},  # /PS-IGNORE
                        {
                            "email": "I1_main_contact_alt_no_notify@example.com",  # /PS-IGNORE
                            "notify": False,
                        },
                    ],
                },
                {
                    "username": "I1_A1_main_contact",
                    "email": [
                        {
                            "email": "I1_A1_main_contact_alt@example.com",  # /PS-IGNORE
                            "notify": True,
                        }
                    ],
                },
                {
                    "username": "I3_inactive_contact",
                    "email": [
                        {
                            "email": "I3_inactive_contact_alt@example.com",  # /PS-IGNORE
                            "notify": True,
                        }
                    ],
                },
                {
                    "username": "E1_main_contact",
                    "email": [
                        {
                            "email": "E1_main_contact_second_email@example.com",  # /PS-IGNORE
                            "notify": True,
                        },
                        {
                            "email": "E1_main_contact_no_notify@example.com",  # /PS-IGNORE
                            "notify": False,
                        },
                        {
                            "email": "E1_main_contact_alt@example.com",  # /PS-IGNORE
                            "notify": True,
                        },
                        {
                            "email": "E1_main_contact_alt_no_notify@example.com",  # /PS-IGNORE
                            "notify": False,
                        },
                    ],
                },
                {
                    "username": "E1_A1_main_contact",
                    "email": [
                        {
                            "email": "E1_A1_main_contact_alt@example.com",  # /PS-IGNORE
                            "notify": True,
                        },
                        {
                            "email": "E1_A1_main_contact_alt_no_notify@example.com",  # /PS-IGNORE
                            "notify": False,
                        },
                    ],
                },
                {
                    "username": "E3_inactive_contact",
                    "email": [
                        {
                            "email": "archived_export_user_alt@example.com",  # /PS-IGNORE
                            "notify": True,
                        }
                    ],
                },
            ],
        )

    def setUp(self):
        self.setup_user_emails()

    def test_send_email(self):
        email.send_email.delay(
            "Test subject",
            "Test message",
            ["test@example.com", "test2@example.com"],  # /PS-IGNORE
            html_message="<p>Test message</p>",
        )
        outbox = mail.outbox
        assert len(outbox) == 1
        assert "test@example.com" in outbox[0].to  # /PS-IGNORE
        assert "test2@example.com" in outbox[0].to  # /PS-IGNORE

    def test_multipart_email(self):
        email.send_email("Subject", "Message", ["test@example.com", "<p>Message</p>"])  # /PS-IGNORE
        m = mail.outbox[0]
        assert isinstance(m, mail.EmailMultiAlternatives)

    def test_mail_subject(self):
        email.send_email("Subject", "Message", ["test@example.com", "<p>Message</p>"])  # /PS-IGNORE
        m = mail.outbox[0]
        assert m.subject == "Subject"

    def test_mail_body(self):
        email.send_email("Subject", "Message", ["test@example.com", "<p>Message</p>"])  # /PS-IGNORE
        m = mail.outbox[0]
        assert m.body == "Message"

    def test_mail_from(self):
        email.send_email("Subject", "Message", ["test@example.com", "<p>Message</p>"])  # /PS-IGNORE
        m = mail.outbox[0]

        # Set in config/settings/non_prod_base.py
        assert m.from_email == "enquiries.ilb@icms.trade.dev.uktrade.io"  # /PS-IGNORE

    def test_mail_to(self):
        email.send_email(
            "Subject",
            "Message",
            ["test@example.com", "test2@example.com", "<p>Message</p>"],  # /PS-IGNORE
        )
        m = mail.outbox[0]
        assert m.to[0] == "test@example.com"  # /PS-IGNORE
        assert m.to[1] == "test2@example.com"  # /PS-IGNORE
