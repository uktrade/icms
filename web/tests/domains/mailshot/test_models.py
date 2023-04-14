from django.test import TestCase

from web.models import Mailshot
from web.tests.domains.user.factory import UserFactory


class TestMailshot(TestCase):
    def create_mailshot(
        self,
        title="Test Mailshot",
        status=Mailshot.Statuses.DRAFT,
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
        assert isinstance(mailshot, Mailshot)
        assert mailshot.title == "Test Mailshot"
        assert mailshot.status == Mailshot.Statuses.DRAFT
        assert mailshot.is_active is True
