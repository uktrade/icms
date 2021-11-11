import pytest
from django.urls import reverse, reverse_lazy
from guardian.shortcuts import assign_perm
from pytest_django.asserts import assertTemplateUsed

from web.domains.case.export.models import ExportApplicationType
from web.domains.cat.models import CertificateApplicationTemplate
from web.domains.country.models import Country
from web.flow.models import Task
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

    def test_redirect_for_template_query_param(self):
        self.login_with_permissions([self.permission])

        template = CertificateApplicationTemplate.objects.create(
            owner=self.user,
            name="CFS template",
            application_type=ExportApplicationType.Types.FREE_SALE,
        )
        url = self.url + f"?from-template={template.pk}"
        response = self.client.get(url)

        assert response.status_code == 302
        assert response["Location"] == f"/export/create/cfs/?from-template={template.pk}"

    def test_no_error_for_invalid_template_query_param(self):
        self.login_with_permissions([self.permission])

        with pytest.raises(CertificateApplicationTemplate.DoesNotExist):
            CertificateApplicationTemplate.objects.get(pk=999)

        url = self.url + "?from-template=999"
        response = self.client.get(url)

        assert response.status_code == 200
        assert [t.name for t in response.templates] == ["web/domains/case/export/choose.html"]


class TestCreateApplication(AuthTestCase):
    permission = "exporter_access"
    url = reverse_lazy("export:create-application", kwargs={"type_code": "com"})

    def test_application_template_from_query_params(self):
        self.login_with_permissions([self.permission])

        template = CertificateApplicationTemplate.objects.create(
            owner=self.user,
            name="Test template",
            application_type="COM",
        )
        url = self.url + f"?from-template={template.pk}"
        response = self.client.get(url)

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/case/export/create.html")
        assert response.context["application_template"] == template

    def test_no_error_for_invalid_application_template_query_param(self):
        self.login_with_permissions([self.permission])

        with pytest.raises(CertificateApplicationTemplate.DoesNotExist):
            CertificateApplicationTemplate.objects.get(pk=999)

        url = self.url + "?from-template=999"
        response = self.client.get(url)

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/case/export/create.html")
        assert response.context["application_template"] is None


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
