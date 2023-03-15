import re

import pytest
from django.urls import reverse, reverse_lazy
from guardian.shortcuts import assign_perm
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
from web.tests.domains.case.export.factories import (
    CertificateOfManufactureApplicationFactory,
)


class TestApplicationChoice(AuthTestCase):
    url = reverse("export:choose")
    permission = "exporter_access"

    def test_create_no_access(self):
        self.login()

        response = self.client.get(self.url)
        assert response.status_code == 403

    def test_create_has_access(self):
        self.login_with_permissions([self.permission])

        response = self.client.get(self.url)
        assert response.status_code == 200


class TestCreateApplication(AuthTestCase):
    permission = "exporter_access"
    url = reverse_lazy("export:create-application", kwargs={"type_code": "com"})

    def test_template_context(self):
        self.login_with_permissions([self.permission])

        response = self.client.get(self.url)

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/case/export/create.html")


class TestCreateApplicationFromTemplate(AuthTestCase):
    permission = "exporter_access"

    def test_404_for_invalid_template_id(self):
        self.login_with_permissions([self.permission])

        with pytest.raises(CertificateApplicationTemplate.DoesNotExist):
            CertificateApplicationTemplate.objects.get(pk=999)

        url = reverse(
            "export:create-application-from-template",
            kwargs={"type_code": "com", "template_pk": 999},
        )
        response = self.client.get(url)

        assert response.status_code == 404

    def test_redirect_for_permission_denied_template(self):
        self.login_with_permissions([self.permission])
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
        response = self.client.get(url)

        assert response.status_code == 302
        assert response["Location"] == "/export/create/cfs/"

    def test_redirect_for_archived_template(self):
        self.login_with_permissions([self.permission])

        template = CertificateApplicationTemplate.objects.create(
            owner=self.user,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
            is_active=False,
        )
        url = reverse(
            "export:create-application-from-template",
            kwargs={"type_code": template.application_type.lower(), "template_pk": template.pk},
        )
        response = self.client.get(url)

        assert response.status_code == 302
        assert response["Location"] == "/export/create/cfs/"


class TestFlow(AuthTestCase):
    def test_flow(self):
        """Assert flow uses process and update tasks."""
        appl = CertificateOfManufactureApplicationFactory.create(status="IN_PROGRESS")
        appl.tasks.create(is_active=True, task_type=Task.TaskType.PREPARE)

        self.login_with_permissions(["exporter_access"])
        assign_perm("web.is_contact_of_exporter", self.user, appl.exporter)

        url_edit = reverse("export:com-edit", kwargs={"application_pk": appl.pk})
        url_submit = reverse("export:com-submit", kwargs={"application_pk": appl.pk})

        response = self.client.post(
            reverse("export:com-edit", kwargs={"application_pk": appl.pk}),
            data={
                "contact": self.user.pk,
                "countries": Country.objects.last().pk,
                "is_pesticide_on_free_sale_uk": "false",
                "is_manufacturer": "true",
                "product_name": "new product export",
                "chemical_name": "some checmical name",
                "manufacturing_process": "squeeze a few drops",
            },
        )

        # when form is submitted it stays on the same url
        self.assertRedirects(response, url_edit)

        # process and task haven't changed
        appl.refresh_from_db()
        self.assertEqual(appl.status, "IN_PROGRESS")
        self.assertEqual(appl.tasks.count(), 1)
        task = appl.tasks.get()
        self.assertEqual(task.task_type, Task.TaskType.PREPARE)
        self.assertEqual(task.is_active, True)

        # declaration of truth
        response = self.client.post(url_submit, data={"confirmation": "I AGREE"})
        self.assertRedirects(response, "/workbasket/")

        appl.refresh_from_db()
        self.assertEqual(appl.status, "SUBMITTED")

        # a new task has been created
        self.assertEqual(appl.tasks.count(), 2)

        # previous task is not active anymore
        prepare_task = appl.tasks.get(task_type=Task.TaskType.PREPARE)
        self.assertEqual(prepare_task.is_active, False)
        appl_task = appl.tasks.get(task_type=Task.TaskType.PROCESS)
        self.assertEqual(appl_task.is_active, True)


class TestEditCom(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.appl = CertificateOfManufactureApplicationFactory.create()
        self.url = reverse("export:com-edit", kwargs={"application_pk": self.appl.pk})

    def test_edit_ok(self):
        self.appl.tasks.create(is_active=True, task_type=Task.TaskType.PREPARE)
        self.login_with_permissions(["exporter_access"])

        assign_perm("web.is_contact_of_exporter", self.user, self.appl.exporter)

        response = self.client.post(
            self.url,
            data={
                "contact": self.user.pk,
                "countries": [Country.objects.last().pk],
                "is_pesticide_on_free_sale_uk": "false",
                "is_manufacturer": "true",
                "product_name": "new product export",
                "chemical_name": "some checmical name",
                "manufacturing_process": "squeeze a few drops",
            },
        )

        self.assertRedirects(
            response,
            reverse("export:com-edit", kwargs={"application_pk": self.appl.pk}),
            fetch_redirect_response=False,
        )

    def test_edit_no_auth(self):
        self.appl.tasks.create(is_active=True, task_type=Task.TaskType.PREPARE)
        self.login_with_permissions(["exporter_access"])

        response = self.client.post(self.url)
        assert response.status_code == 403

    def test_no_task(self):
        """Assert an application/flow requires an active task."""
        self.login_with_permissions(["exporter_access"])
        assign_perm("web.is_contact_of_exporter", self.user, self.appl.exporter)

        with self.assertRaises(Exception, msg="Expected one active task, got 0"):
            self.client.get(self.url)


class TestSubmitCom(AuthTestCase):
    def setUp(self):
        super().setUp()
        # Make the application valid (now we have a validation summary)
        self.appl = CertificateOfManufactureApplicationFactory.create()
        self.appl.contact = self.user
        self.appl.countries.add(Country.objects.all().first())
        self.appl.is_pesticide_on_free_sale_uk = False
        self.appl.is_manufacturer = True
        self.appl.product_name = "new product export"
        self.appl.chemical_name = "some chemical name"
        self.appl.manufacturing_process = "squeeze a few drops"
        self.appl.save()
        self.url = reverse("export:com-submit", kwargs={"application_pk": self.appl.pk})

    def test_submit_ok(self):
        self.appl.tasks.create(is_active=True, task_type=Task.TaskType.PREPARE)
        self.login_with_permissions(["exporter_access"])
        assign_perm("web.is_contact_of_exporter", self.user, self.appl.exporter)

        response = self.client.post(self.url, data={"confirmation": "I AGREE"})
        self.assertRedirects(response, "/workbasket/", fetch_redirect_response=False)

    def test_submit_no_auth(self):
        self.appl.tasks.create(is_active=True, task_type=Task.TaskType.PREPARE)
        self.login_with_permissions(["exporter_access"])

        response = self.client.post(self.url, data={"confirmation": "I AGREE"})
        assert response.status_code == 403

    def test_submit_not_agreed(self):
        self.appl.tasks.create(is_active=True, task_type=Task.TaskType.PREPARE)
        self.login_with_permissions(["exporter_access"])
        assign_perm("web.is_contact_of_exporter", self.user, self.appl.exporter)

        response = self.client.post(self.url, data={"confirmation": "NOPE"})
        assert response.status_code == 200

        print(response.content.decode())

        assert "Please agree to the declaration of truth." in response.content.decode()

    def test_no_task(self):
        """Assert an application/flow requires an active task."""
        self.login_with_permissions(["exporter_access"])
        assign_perm("web.is_contact_of_exporter", self.user, self.appl.exporter)

        with self.assertRaises(Exception, msg="Expected one active task, got 0"):
            self.client.get(self.url)


def test_create_csf_app_has_a_schedule(exporter_client, exporter, exporter_office):
    url = reverse("export:create-application", kwargs={"type_code": "cfs"})
    data = {"exporter": exporter.pk, "exporter_office": exporter_office.pk}

    response = exporter_client.post(url, data)

    application_pk = re.search(r"\d+", response.url).group(0)
    expected_url = reverse("export:cfs-edit", kwargs={"application_pk": application_pk})
    assertRedirects(response, expected_url, 302)

    cfs_app = CertificateOfFreeSaleApplication.objects.get(pk=application_pk)
    assert cfs_app.schedules.count() == 1
