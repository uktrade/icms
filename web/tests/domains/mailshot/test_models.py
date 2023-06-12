from web.models import Mailshot
from web.tests.auth import AuthTestCase


class TestMailshot(AuthTestCase):
    def create_mailshot(
        self,
        title="Test Mailshot",
        status=Mailshot.Statuses.DRAFT,
        is_retraction_email=False,
        is_active=True,
    ):
        return Mailshot.objects.create(
            title=title,
            status=status,
            is_retraction_email=is_retraction_email,
            created_by=self.importer_user,
            is_active=is_active,
        )

    def test_create_mailshot(self):
        mailshot = self.create_mailshot()
        assert isinstance(mailshot, Mailshot)
        assert mailshot.title == "Test Mailshot"
        assert mailshot.status == Mailshot.Statuses.DRAFT
        assert mailshot.is_active is True
