import pytest

from web.models import CertificateApplicationTemplate, User


@pytest.mark.django_db
class TestCertificateApplicationTemplate:
    def test_owner_user_can_view(self):
        alice = User.objects.create_user("alice")
        bob = User.objects.create_user("bob")
        template = CertificateApplicationTemplate(owner=alice)

        assert template.user_can_view(bob) is False
        assert template.user_can_view(alice) is True

    def test_owner_user_can_edit(self):
        alice = User.objects.create_user("alice")
        bob = User.objects.create_user("bob")
        template = CertificateApplicationTemplate(owner=alice)

        assert template.user_can_edit(bob) is False
        assert template.user_can_edit(alice) is True
