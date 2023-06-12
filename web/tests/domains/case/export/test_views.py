import re

import pytest
from django.urls import reverse, reverse_lazy
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from web.models import (
    CertificateApplicationTemplate,
    CertificateOfFreeSaleApplication,
    Country,
    ExportApplicationType,
    Task,
    User,
)
from web.tests.auth.auth import AuthTestCase


class TestApplicationChoice(AuthTestCase):
    url = reverse("export:choose")

    def test_create_no_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

    def test_create_has_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 200


class TestCreateApplication(AuthTestCase):
    url = reverse_lazy("export:create-application", kwargs={"type_code": "com"})

    def test_template_context(self):
        response = self.exporter_client.get(self.url)

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/case/export/create.html")


class TestCreateApplicationFromTemplate(AuthTestCase):
    def test_404_for_invalid_template_id(self):
        assert not CertificateApplicationTemplate.objects.filter(pk=999).exists()
        url = reverse(
            "export:create-application-from-template",
            kwargs={"type_code": "com", "template_pk": 999},
        )
        response = self.exporter_client.get(url)

        assert response.status_code == 404

    def test_redirect_for_permission_denied_template(self):
        alice = User.objects.create_user("alice")

        template = CertificateApplicationTemplate.objects.create(
            owner=alice,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
        )
        url = reverse(
            "export:create-application-from-template",
            kwargs={"type_code": template.application_type.lower(), "template_pk": template.pk},
        )
        response = self.exporter_client.get(url)

        assert response.status_code == 302
        assert response["Location"] == "/export/create/cfs/"

    def test_redirect_for_archived_template(self):
        template = CertificateApplicationTemplate.objects.create(
            owner=self.exporter_user,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
            is_active=False,
        )
        url = reverse(
            "export:create-application-from-template",
            kwargs={"type_code": template.application_type.lower(), "template_pk": template.pk},
        )
        response = self.exporter_client.get(url)

        assert response.status_code == 302
        assert response["Location"] == "/export/create/cfs/"


class TestFlow(AuthTestCase):
    def test_flow(self, com_app_in_progress):
        """Assert flow uses process and update tasks."""
        appl = com_app_in_progress
        url_edit = reverse("export:com-edit", kwargs={"application_pk": appl.pk})
        url_submit = reverse("export:com-submit", kwargs={"application_pk": appl.pk})

        response = self.exporter_client.post(
            reverse("export:com-edit", kwargs={"application_pk": appl.pk}),
            data={
                "contact": self.exporter_user.pk,
                "countries": Country.objects.last().pk,
                "is_pesticide_on_free_sale_uk": "false",
                "is_manufacturer": "true",
                "product_name": "new product export",
                "chemical_name": "some checmical name",
                "manufacturing_process": "squeeze a few drops",
            },
        )

        # when form is submitted it stays on the same url
        assertRedirects(response, url_edit)

        # process and task haven't changed
        appl.refresh_from_db()
        assert appl.status == "IN_PROGRESS"
        assert appl.tasks.count() == 1
        task = appl.tasks.get()
        assert task.task_type == Task.TaskType.PREPARE
        assert task.is_active is True

        # declaration of truth
        response = self.exporter_client.post(url_submit, data={"confirmation": "I AGREE"})
        assertRedirects(response, "/workbasket/")

        appl.refresh_from_db()
        assert appl.status == "SUBMITTED"

        # a new task has been created
        assert appl.tasks.count() == 2

        # previous task is not active anymore
        prepare_task = appl.tasks.get(task_type=Task.TaskType.PREPARE)
        assert prepare_task.is_active is False
        appl_task = appl.tasks.get(task_type=Task.TaskType.PROCESS)
        assert appl_task.is_active is True


class TestEditCom(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, com_app_in_progress):
        self.appl = com_app_in_progress
        self.url = reverse("export:com-edit", kwargs={"application_pk": self.appl.pk})

    def test_edit_ok(self):
        self.appl.tasks.create(is_active=True, task_type=Task.TaskType.PREPARE)

        response = self.exporter_client.post(
            self.url,
            data={
                "contact": self.exporter_user.pk,
                "countries": [Country.objects.last().pk],
                "is_pesticide_on_free_sale_uk": "false",
                "is_manufacturer": "true",
                "product_name": "new product export",
                "chemical_name": "some checmical name",
                "manufacturing_process": "squeeze a few drops",
            },
        )

        assertRedirects(
            response,
            reverse("export:com-edit", kwargs={"application_pk": self.appl.pk}),
            fetch_redirect_response=False,
        )

    def test_edit_no_auth(self):
        self.appl.tasks.create(is_active=True, task_type=Task.TaskType.PREPARE)

        response = self.importer_client.post(self.url)
        assert response.status_code == 403

    def test_no_task(self):
        """Assert an application/flow requires an active task."""
        self.appl.tasks.all().delete()
        with pytest.raises(Exception, match="prepare not in active task list"):
            self.exporter_client.get(self.url)


class TestSubmitCom(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, com_app_in_progress):
        # Make the application valid (now we have a validation summary)
        self.appl = com_app_in_progress
        self.appl.contact = self.exporter_user
        self.appl.countries.add(Country.objects.all().first())
        self.appl.is_pesticide_on_free_sale_uk = False
        self.appl.is_manufacturer = True
        self.appl.product_name = "new product export"
        self.appl.chemical_name = "some chemical name"
        self.appl.manufacturing_process = "squeeze a few drops"
        self.appl.save()
        self.url = reverse("export:com-submit", kwargs={"application_pk": self.appl.pk})

    def test_submit_ok(self):
        response = self.exporter_client.post(self.url, data={"confirmation": "I AGREE"})
        assertRedirects(response, "/workbasket/", fetch_redirect_response=False)

    def test_submit_no_auth(self):
        response = self.importer_client.post(self.url, data={"confirmation": "I AGREE"})
        assert response.status_code == 403

    def test_submit_not_agreed(self):
        response = self.exporter_client.post(self.url, data={"confirmation": "NOPE"})
        assert response.status_code == 200

        assert "Please agree to the declaration of truth." in response.content.decode()

    def test_no_task(self):
        """Assert an application/flow requires an active task."""
        self.appl.tasks.all().delete()
        with pytest.raises(Exception, match="prepare not in active task list"):
            self.exporter_client.get(self.url)


def test_create_csf_app_has_a_schedule(exporter_client, exporter, exporter_office):
    url = reverse("export:create-application", kwargs={"type_code": "cfs"})
    data = {"exporter": exporter.pk, "exporter_office": exporter_office.pk}

    response = exporter_client.post(url, data)

    application_pk = re.search(r"\d+", response.url).group(0)
    expected_url = reverse("export:cfs-edit", kwargs={"application_pk": application_pk})
    assertRedirects(response, expected_url, 302)

    cfs_app = CertificateOfFreeSaleApplication.objects.get(pk=application_pk)
    assert cfs_app.schedules.count() == 1
