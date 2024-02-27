import pytest
from django.urls import reverse, reverse_lazy
from pytest_django.asserts import assertTemplateUsed

from web.domains.cat.forms import CATFilter
from web.models import (
    CertificateApplicationTemplate,
    CertificateOfManufactureApplicationTemplate,
    ExportApplicationType,
)
from web.tests.auth import AuthTestCase


class TestCATListView(AuthTestCase):
    url = reverse_lazy("cat:list")

    def test_template_context(self):
        response = self.exporter_client.get(self.url)

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/cat/list.html")

        assert isinstance(response.context["filter"], CATFilter)

    def test_filter_queryset_by_name(self):
        for name in ("Foo", "Bar", "Baz"):
            CertificateApplicationTemplate.objects.create(
                owner=self.exporter_user,
                name=name,
                application_type=ExportApplicationType.Types.GMP,
            )

        # Filtering with query parameters.
        response = self.exporter_client.get(self.url, {"name": "foo"})

        assert response.status_code == 200
        assert [t.name for t in response.context["templates"]] == ["Foo"]

    def test_filter_defaults_to_current_templates(self):
        foo = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="foo",
            application_type=ExportApplicationType.Types.GMP,
            is_active=True,
        )
        CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="bar",
            application_type=ExportApplicationType.Types.GMP,
            is_active=False,
        )

        response = self.exporter_client.get(self.url, {})

        assert response.status_code == 200
        # The archived template is not shown.
        assert [t.pk for t in response.context["templates"]] == [foo.pk]


class TestCATCreateView(AuthTestCase):
    def test_can_create_template(self):
        with pytest.raises(CertificateApplicationTemplate.DoesNotExist):
            CertificateApplicationTemplate.objects.get()

        url = reverse("cat:create")
        data = {
            "name": "Foo name",
            "description": "Foo description",
            "application_type": "CFS",
            "sharing": "private",
        }
        response = self.exporter_client.post(url, data)

        assert response.status_code == 302
        assert response["Location"] == "/cat/"

        template = CertificateApplicationTemplate.objects.get()
        assert template.name == "Foo name"


class TestCATEditView(AuthTestCase):
    def test_show_edit_form(self):
        cat = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
        )
        CertificateOfManufactureApplicationTemplate.objects.create(template=cat)
        url = reverse("cat:edit", kwargs={"cat_pk": cat.pk})

        response = self.exporter_client.get(url)

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/cat/edit.html")

    def test_permission_denied(self):
        cat = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
        )
        CertificateOfManufactureApplicationTemplate.objects.create(template=cat)
        url = reverse("cat:edit", kwargs={"cat_pk": cat.pk})

        response = self.importer_client.get(url)

        assert response.status_code == 403


class TestCATEditStepView(AuthTestCase):
    def test_show_edit_step_form(self):
        cat = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
        )
        CertificateOfManufactureApplicationTemplate.objects.create(template=cat)

        url = reverse("cat:edit-step", kwargs={"cat_pk": cat.pk, "step": "cfs"})

        response = self.exporter_client.get(url)

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/cat/edit.html")


class TestCATArchiveView(AuthTestCase):
    def test_archive_a_template(self):
        cat = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="GMP template",
            application_type=ExportApplicationType.Types.GMP,
        )
        CertificateOfManufactureApplicationTemplate.objects.create(template=cat)
        assert cat.is_active is True

        url = reverse("cat:archive", kwargs={"cat_pk": cat.pk})
        response = self.exporter_client.post(url)

        assert response.status_code == 302
        assert response["Location"] == "/cat/"

        cat.refresh_from_db()

        assert cat.is_active is False

    def test_permission_denied(self):
        cat = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
        )
        CertificateOfManufactureApplicationTemplate.objects.create(template=cat)
        url = reverse("cat:archive", kwargs={"cat_pk": cat.pk})

        response = self.importer_client.get(url)

        assert response.status_code == 403


class TestCATRestoreView(AuthTestCase):
    def test_restore_a_template(self):
        cat = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="GMP template",
            application_type=ExportApplicationType.Types.GMP,
            is_active=False,
        )
        CertificateOfManufactureApplicationTemplate.objects.create(template=cat)
        assert cat.is_active is False

        url = reverse("cat:restore", kwargs={"cat_pk": cat.pk})
        response = self.exporter_client.post(url)

        assert response.status_code == 302
        assert response["Location"] == "/cat/"

        cat.refresh_from_db()

        assert cat.is_active is True

    def test_permission_denied(self):
        cat = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
            is_active=False,
        )
        CertificateOfManufactureApplicationTemplate.objects.create(template=cat)
        url = reverse("cat:restore", kwargs={"cat_pk": cat.pk})

        response = self.importer_client.get(url)

        assert response.status_code == 403


class TestCATReadOnlyView(AuthTestCase):
    def test_show_disabled_form_for_template(self):
        cat = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
        )
        CertificateOfManufactureApplicationTemplate.objects.create(template=cat)
        url = reverse("cat:view", kwargs={"cat_pk": cat.pk})

        response = self.exporter_client.get(url)

        assert response.status_code == 200
        assert response.context["read_only"] is True

    def test_show_disabled_form_for_step(self):
        cat = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
        )
        CertificateOfManufactureApplicationTemplate.objects.create(template=cat)
        url = reverse("cat:view-step", kwargs={"cat_pk": cat.pk, "step": "cfs"})

        response = self.exporter_client.get(url)

        assert response.status_code == 200
        assert response.context["read_only"] is True
