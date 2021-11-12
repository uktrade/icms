import pytest

from web.domains.cat.models import CertificateApplicationTemplate
from web.domains.user.models import User


@pytest.mark.django_db
class TestCertificateApplicationTemplate:
    def test_form_data_makes_a_copy(self):
        original = {"foo": "bar"}
        obj = CertificateApplicationTemplate(data=original)
        data = obj.form_data()
        data["foo"] = "qux"

        assert original == {"foo": "bar"}

    def test_owner_user_can_view(self):
        alice = User.objects.create_user("alice")
        bob = User.objects.create_user("bob")
        template = CertificateApplicationTemplate(owner=alice)

        assert template.user_can_view(bob) is False
        assert template.user_can_view(alice) is True
