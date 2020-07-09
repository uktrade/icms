from django.test import TestCase

from web.domains.mailshot.models import Mailshot
from web.tests.domains.user.factory import UserFactory


class MailshotTest(TestCase):
    def create_mailshot(
        self,
        title="Test Mailshot",
        status=Mailshot.DRAFT,
        is_retraction_email=False,
        is_active=True,
    ):
        user = UserFactory()
        return Mailshot.objects.create(
            title=title,
            status=status,
            is_retraction_email=is_retraction_email,
            created_by=user,
            is_active=is_active,
        )

    def test_create_mailshot(self):
        mailshot = self.create_mailshot()
        self.assertTrue(isinstance(mailshot, Mailshot))
        self.assertEqual(mailshot.title, "Test Mailshot")
        self.assertEqual(mailshot.status, Mailshot.DRAFT)
        self.assertTrue(mailshot.is_active)
