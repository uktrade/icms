import pytest

from web.models import CertificateApplicationTemplate, User


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

    def test_owner_user_can_edit(self):
        alice = User.objects.create_user("alice")
        bob = User.objects.create_user("bob")
        template = CertificateApplicationTemplate(owner=alice)

        assert template.user_can_edit(bob) is False
        assert template.user_can_edit(alice) is True

    # TODO: ICMSLST-2520 Uncomment this test to fix bug where application hangs.
    # def test_json_serialization_of_models(self):
    #     alice = User.objects.create_user("alice")
    #     data = {
    #         "alice": alice,
    #         "objects": User.objects.filter(username="alice"),
    #     }
    #     # This line causes the application to hang forever in psycopg 3.
    #     # I think it relates to evaluating this line when creating the template
    #     # record: User.objects.filter(username="alice")
    #     template = CertificateApplicationTemplate.objects.create(
    #         owner=alice,
    #         data=data,
    #     )
    #     template.refresh_from_db()
    #
    #     assert template.form_data() == {"alice": alice.pk, "objects": [alice.pk]}
