import pytest

from web.domains.case.export.models import ExportApplicationType
from web.domains.cat.models import CertificateApplicationTemplate
from web.models import User


@pytest.mark.django_db
class TestCATObjectsManager:
    def test_objects_active(self):
        alice = User.objects.create_user("alice")
        foo = CertificateApplicationTemplate.objects.create(
            owner=alice,
            name="foo",
            application_type=ExportApplicationType.Types.GMP,
            is_active=True,
        )
        CertificateApplicationTemplate.objects.create(
            owner=alice,
            name="bar",
            application_type=ExportApplicationType.Types.GMP,
            is_active=False,
        )
        queryset = CertificateApplicationTemplate.objects.active()

        assert [o.pk for o in queryset] == [foo.pk]

    def test_objects_inactive(self):
        alice = User.objects.create_user("alice")
        CertificateApplicationTemplate.objects.create(
            owner=alice,
            name="foo",
            application_type=ExportApplicationType.Types.GMP,
            is_active=True,
        )
        bar = CertificateApplicationTemplate.objects.create(
            owner=alice,
            name="bar",
            application_type=ExportApplicationType.Types.GMP,
            is_active=False,
        )
        queryset = CertificateApplicationTemplate.objects.inactive()

        assert [o.pk for o in queryset] == [bar.pk]
