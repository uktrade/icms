from http import HTTPStatus

import pytest
from django.urls import reverse
from guardian.shortcuts import remove_perm
from pytest_django.asserts import assertInHTML, assertTemplateUsed

from web.ecil.gds import forms as gds_forms
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    Country,
    ECILUserExportApplication,
)
from web.models.shared import YesNoChoices
from web.permissions import get_org_obj_permissions


class TestCreateExportApplicationStartTemplateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:export-application:new")
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post_forbidden(self):
        response = self.client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/start.html")
        assert response.context["pick_app_type_url"] == reverse(
            "ecil:export-application:application-type"
        )


class TestCreateExportApplicationAppTypeFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:export-application:application-type")
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        # No record exists until page viewed
        assert not ECILUserExportApplication.objects.filter(created_by=self.user).exists()

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        # Record exists after page viewed
        assert ECILUserExportApplication.objects.filter(created_by=self.user).exists()
        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:new"
        )

    def test_post(self):
        # Test error message
        form_data = {"app_type": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "app_type": ["Select the certificate you are applying for."],
        }

        # Check record exists but no app type set
        record = ECILUserExportApplication.objects.get(created_by=self.user)
        assert record.app_type == ""

        # Test post success
        form_data = {"app_type": "cfs"}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:exporter")

        record.refresh_from_db()
        assert record.app_type == "cfs"


class TestCreateExportApplicationExporterFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:export-application:exporter")
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        # No record exists until page viewed
        assert not ECILUserExportApplication.objects.filter(created_by=self.user).exists()

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        # Record exists after page viewed
        assert ECILUserExportApplication.objects.filter(created_by=self.user).exists()
        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:application-type"
        )

    def test_post(self, exporter):
        # Test error message
        form_data = {"exporter": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "exporter": ["Select the company you want an export certificate for."],
        }

        # Check record exists but no exporter set
        record = ECILUserExportApplication.objects.get(created_by=self.user)
        assert record.exporter is None

        # Test post success (None of These chosen)
        form_data = {"exporter": gds_forms.GovUKRadioInputField.NONE_OF_THESE}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:another-exporter")

        record.refresh_from_db()
        assert record.exporter is None

        # Test post success (exporter set)
        form_data = {"exporter": exporter.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:exporter-office")

        record.refresh_from_db()
        assert record.exporter == exporter


class TestCreateExportApplicationExporterOfficeFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:export-application:exporter-office")
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        # No record exists until page viewed
        assert not ECILUserExportApplication.objects.filter(created_by=self.user).exists()

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        # Record exists after page viewed
        assert ECILUserExportApplication.objects.filter(created_by=self.user).exists()
        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter"
        )

    def test_post(self, exporter, exporter_office):
        # Test error message
        form_data = {"exporter_office": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "exporter_office": ["Select the address you want an export certificate for."],
        }

        # Check record exists but no exporter office set
        record = ECILUserExportApplication.objects.get(created_by=self.user)
        assert record.exporter_office is None

        # Save an exporter to the record (to populate the office list)
        record.exporter = exporter
        record.save()

        # Test post success (None of These chosen)
        form_data = {"exporter_office": gds_forms.GovUKRadioInputField.NONE_OF_THESE}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:exporter-office-add")

        record.refresh_from_db()
        assert record.exporter_office is None

        # Test post success (exporter office set)
        form_data = {"exporter_office": exporter_office.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:summary")

        record.refresh_from_db()
        assert record.exporter_office == exporter_office

        # Test removing edit & manage permissions returns a different success url
        obj_perms = get_org_obj_permissions(exporter)
        remove_perm(obj_perms.edit, self.user, exporter)
        remove_perm(obj_perms.manage_contacts_and_agents, self.user, exporter)

        form_data = {"exporter_office": gds_forms.GovUKRadioInputField.NONE_OF_THESE}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:another-exporter-office")

        record.refresh_from_db()
        assert record.exporter_office is None

    def test_agent_post(
        self, prototype_export_agent_client, prototype_export_agent_user, exporter, exporter_office
    ):
        # Setup - use the export agent client / user
        client = prototype_export_agent_client
        user = prototype_export_agent_user

        # Setup - save exporter to ECILUserExportApplication record
        record = ECILUserExportApplication.objects.create(created_by=user)
        record.exporter = exporter
        record.save()

        # Test post success (exporter office set)
        form_data = {"exporter_office": exporter_office.pk}
        response = client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        record.refresh_from_db()
        assert record.exporter_office == exporter_office

        # assert url redirects to set agent exporter view
        assert response.url == reverse("ecil:export-application:exporter-agent")


class TestCreateExportApplicationExporterAgentFormView:
    @pytest.fixture(autouse=True)
    def setup(
        self, prototype_export_agent_client, prototype_export_agent_user, exporter, exporter_office
    ):
        self.user = prototype_export_agent_user
        self.url = reverse("ecil:export-application:exporter-agent")
        self.client = prototype_export_agent_client
        self.record = ECILUserExportApplication.objects.create(
            created_by=self.user, exporter=exporter, exporter_office=exporter_office
        )

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter-office"
        )

    def test_post(self, agent_exporter):
        # Test error message
        form_data = {"agent": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "agent": ["Select the company you want an export certificate for."],
        }

        # Check record exists but no agent set
        record = ECILUserExportApplication.objects.get(created_by=self.user)
        assert record.agent is None

        # Test post success (None of These chosen)
        form_data = {"agent": gds_forms.GovUKRadioInputField.NONE_OF_THESE}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:another-exporter")

        record.refresh_from_db()
        assert record.agent is None

        # Test post success (agent set)
        form_data = {"agent": agent_exporter.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:exporter-agent-office")

        record.refresh_from_db()
        assert record.agent == agent_exporter


class TestCreateExportApplicationExporterAgentOfficeFormView:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        prototype_export_agent_client,
        prototype_export_agent_user,
        exporter,
        exporter_office,
        agent_exporter,
    ):
        self.user = prototype_export_agent_user
        self.url = reverse("ecil:export-application:exporter-agent-office")
        self.client = prototype_export_agent_client
        self.record = ECILUserExportApplication.objects.create(
            created_by=self.user,
            exporter=exporter,
            exporter_office=exporter_office,
            agent=agent_exporter,
        )

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter-agent"
        )

    def test_post(self, agent_exporter, exporter_one_agent_one_office):
        # Test error message
        form_data = {"agent_office": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "agent_office": ["Select the agent company's offices address."],
        }

        # Check record exists but no exporter office set
        assert self.record.agent_office is None

        # Test post success (None of These chosen)
        form_data = {"agent_office": gds_forms.GovUKRadioInputField.NONE_OF_THESE}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:exporter-agent-office-add")

        self.record.refresh_from_db()
        assert self.record.agent_office is None

        # Test post success (exporter agent office set)
        form_data = {"agent_office": exporter_one_agent_one_office.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:summary")

        self.record.refresh_from_db()
        assert self.record.agent_office == exporter_one_agent_one_office

        # Test removing edit permission returns a different success url
        obj_perms = get_org_obj_permissions(agent_exporter)
        remove_perm(obj_perms.edit, self.user, agent_exporter)

        form_data = {"agent_office": gds_forms.GovUKRadioInputField.NONE_OF_THESE}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:another-exporter-office")

        self.record.refresh_from_db()
        assert self.record.agent_office is None


class TestCreateExportApplicationSummaryUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:export-application:summary")
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self, exporter, exporter_office):
        # No record exists until page viewed
        assert not ECILUserExportApplication.objects.filter(created_by=self.user).exists()

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_summary_list.html")

        # Record exists after page viewed
        record = ECILUserExportApplication.objects.get(created_by=self.user)
        context = response.context

        assert context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter-office"
        )

        # Check context before entering any data
        assert context["summary_list_kwargs"] == {
            "rows": [
                {
                    "key": {"text": "Which certificate are you applying for?"},
                    "value": {"text": "No value entered (Fix in ECIL-618)"},
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:application-type")
                                + "?from_summary=true",
                                "visuallyHiddenText": "app_type",
                            }
                        ]
                    },
                },
                {
                    "key": {"text": "Which company do you want an export certificate for?"},
                    "value": {"text": "No value entered (Fix in ECIL-618)"},
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:exporter")
                                + "?from_summary=true",
                                "visuallyHiddenText": "exporter",
                            }
                        ]
                    },
                },
                {
                    "key": {"text": "Where will the certificate be issued to?"},
                    "value": {"text": "No value entered (Fix in ECIL-618)"},
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:exporter-office")
                                + "?from_summary=true",
                                "visuallyHiddenText": "exporter_office",
                            }
                        ]
                    },
                },
            ]
        }

        # Set the exporter and office and test the context again
        record.app_type = "cfs"
        record.exporter = exporter
        record.exporter_office = exporter_office
        record.save()

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        context = response.context

        assert context["summary_list_kwargs"] == {
            "rows": [
                {
                    "key": {"text": "Which certificate are you applying for?"},
                    "value": {"text": "Certificate of Free Sale (CFS)"},
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:application-type")
                                + "?from_summary=true",
                                "visuallyHiddenText": "app_type",
                            }
                        ]
                    },
                },
                {
                    "key": {"text": "Which company do you want an export certificate for?"},
                    "value": {"text": "Test Exporter 1"},
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:exporter")
                                + "?from_summary=true",
                                "visuallyHiddenText": "exporter",
                            }
                        ]
                    },
                },
                {
                    "key": {"text": "Where will the certificate be issued to?"},
                    "value": {
                        "html": "E1 address line 1<br>E1 address line 2<br>HG15DB",  # /PS-IGNORE
                    },
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:exporter-office")
                                + "?from_summary=true",
                                "visuallyHiddenText": "exporter_office",
                            }
                        ]
                    },
                },
            ]
        }

    def test_post_cfs(self, exporter, exporter_office):
        # Test error messages
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "app_type": ["You must enter this item"],
            "exporter": ["You must enter this item"],
            "exporter_office": ["You must enter this item"],
        }

        # set up record for post
        record = ECILUserExportApplication.objects.get(created_by=self.user)
        record.app_type = "cfs"
        record.exporter = exporter
        record.exporter_office = exporter_office
        record.save()

        # Test post success
        previous_cfs_count = CertificateOfFreeSaleApplication.objects.count()
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        assert CertificateOfFreeSaleApplication.objects.count() == previous_cfs_count + 1
        kwargs = {"application_pk": CertificateOfFreeSaleApplication.objects.last().pk}
        assert response.url == reverse("ecil:export-cfs:application-reference", kwargs=kwargs)

    def test_post_com(self, exporter, exporter_office):
        # Test error messages
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "app_type": ["You must enter this item"],
            "exporter": ["You must enter this item"],
            "exporter_office": ["You must enter this item"],
        }

        # set up record for post
        record = ECILUserExportApplication.objects.get(created_by=self.user)
        record.app_type = "com"
        record.exporter = exporter
        record.exporter_office = exporter_office
        record.save()

        # Test post success
        previous_com_count = CertificateOfManufactureApplication.objects.count()
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        assert CertificateOfManufactureApplication.objects.count() == previous_com_count + 1
        com_app = CertificateOfManufactureApplication.objects.last()
        kwargs = {"application_pk": com_app.pk}
        assert response.url == reverse(com_app.get_edit_view_name(), kwargs=kwargs)

    def test_post_gmp(self, exporter, exporter_office):
        # Test error messages
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "app_type": ["You must enter this item"],
            "exporter": ["You must enter this item"],
            "exporter_office": ["You must enter this item"],
        }

        # set up record for post
        record = ECILUserExportApplication.objects.get(created_by=self.user)
        record.app_type = "gmp"
        record.exporter = exporter
        record.exporter_office = exporter_office
        record.save()

        # Test post success
        previous_gmp_count = CertificateOfGoodManufacturingPracticeApplication.objects.count()
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        assert (
            CertificateOfGoodManufacturingPracticeApplication.objects.count()
            == previous_gmp_count + 1
        )
        gmp_app = CertificateOfGoodManufacturingPracticeApplication.objects.last()
        kwargs = {"application_pk": gmp_app.pk}
        assert response.url == reverse(gmp_app.get_edit_view_name(), kwargs=kwargs)


class TestCreateExportApplicationSummaryUpdateViewAgentApplication:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        prototype_export_agent_client,
        prototype_export_agent_user,
        exporter,
        exporter_office,
        agent_exporter,
        exporter_one_agent_one_office,
    ):
        self.user = prototype_export_agent_user
        self.url = reverse("ecil:export-application:summary")
        self.client = prototype_export_agent_client
        self.record = ECILUserExportApplication.objects.create(
            created_by=self.user,
            exporter=exporter,
            exporter_office=exporter_office,
            agent=agent_exporter,
            agent_office=exporter_one_agent_one_office,
        )

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self, exporter, exporter_office):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_summary_list.html")

        context = response.context

        assert context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter-agent-office"
        )

        assert context["summary_list_kwargs"] == {
            "rows": [
                {
                    "key": {"text": "Which certificate are you applying for?"},
                    "value": {"text": "No value entered (Fix in ECIL-618)"},
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:application-type")
                                + "?from_summary=true",
                                "visuallyHiddenText": "app_type",
                            }
                        ]
                    },
                },
                {
                    "key": {"text": "Which company do you want an export certificate for?"},
                    "value": {"text": "Test Exporter 1"},
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:exporter")
                                + "?from_summary=true",
                                "visuallyHiddenText": "exporter",
                            }
                        ]
                    },
                },
                {
                    "key": {"text": "Where will the certificate be issued to?"},
                    "value": {
                        "html": "E1 address line 1<br>E1 address line 2<br>HG15DB",  # /PS-IGNORE
                    },
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:exporter-office")
                                + "?from_summary=true",
                                "visuallyHiddenText": "exporter_office",
                            }
                        ]
                    },
                },
                {
                    "key": {"text": "Which agent company are you working for?"},
                    "value": {"text": "Test Exporter 1 Agent 1"},
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:exporter-agent")
                                + "?from_summary=true",
                                "visuallyHiddenText": "agent",
                            }
                        ]
                    },
                },
                {
                    "key": {"text": "What is the agent company’s office address?"},
                    "value": {
                        "html": "E1_A1 address line 1<br>E1_A1 address line 2<br>WF43ER",  # /PS-IGNORE
                    },
                    "actions": {
                        "items": [
                            {
                                "text": "Change",
                                "href": reverse("ecil:export-application:exporter-agent-office")
                                + "?from_summary=true",
                                "visuallyHiddenText": "agent_office",
                            }
                        ]
                    },
                },
            ]
        }

    def test_post_cfs(self, agent_exporter, exporter_one_agent_one_office):
        # Clear the agent fields to test they are required.
        self.record.agent = None
        self.record.agent_office = None
        self.record.save()

        # Test error messages
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "app_type": ["You must enter this item"],
            "agent": ["You must enter this item"],
            "agent_office": ["You must enter this item"],
        }

        # set up record for post
        self.record.app_type = "cfs"
        self.record.agent = agent_exporter
        self.record.agent_office = exporter_one_agent_one_office
        self.record.save()

        # Test post success
        previous_cfs_count = CertificateOfFreeSaleApplication.objects.count()
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        assert CertificateOfFreeSaleApplication.objects.count() == previous_cfs_count + 1
        cfs_app = CertificateOfFreeSaleApplication.objects.last()
        kwargs = {"application_pk": cfs_app.pk}
        assert response.url == reverse("ecil:export-cfs:application-reference", kwargs=kwargs)

        assert cfs_app.agent == agent_exporter
        assert cfs_app.agent_office == exporter_one_agent_one_office

    def test_post_com(self, agent_exporter, exporter_one_agent_one_office):
        # set up record for post
        self.record.app_type = "com"
        self.record.save()

        # Test post success
        previous_com_count = CertificateOfManufactureApplication.objects.count()
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        assert CertificateOfManufactureApplication.objects.count() == previous_com_count + 1
        com_app = CertificateOfManufactureApplication.objects.last()
        kwargs = {"application_pk": com_app.pk}
        assert response.url == reverse(com_app.get_edit_view_name(), kwargs=kwargs)

        assert com_app.agent == agent_exporter
        assert com_app.agent_office == exporter_one_agent_one_office

    def test_post_gmp(self, agent_exporter, exporter_one_agent_one_office):
        # set up record for post
        self.record.app_type = "gmp"
        self.record.save()

        # Test post success
        previous_gmp_count = CertificateOfGoodManufacturingPracticeApplication.objects.count()
        response = self.client.post(self.url)
        assert response.status_code == HTTPStatus.FOUND

        assert (
            CertificateOfGoodManufacturingPracticeApplication.objects.count()
            == previous_gmp_count + 1
        )
        gmp_app = CertificateOfGoodManufacturingPracticeApplication.objects.last()
        kwargs = {"application_pk": gmp_app.pk}
        assert response.url == reverse(gmp_app.get_edit_view_name(), kwargs=kwargs)

        assert gmp_app.agent == agent_exporter
        assert gmp_app.agent_office == exporter_one_agent_one_office


class TestCreateExportApplicationExporterOfficeCreateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:export-application:exporter-office-add")
        self.client = prototype_export_client
        self.user_export_app, _ = ECILUserExportApplication.objects.get_or_create(
            created_by=self.user
        )

    def test_permission(self, ilb_admin_client, exporter):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        # Requires a linked exporter set to have permission to view.
        self.user_export_app.exporter = exporter
        self.user_export_app.save()

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        # Requires edit access at organisation (so removing it should return forbidden)
        obj_perms = get_org_obj_permissions(exporter)
        remove_perm(obj_perms.edit, self.user, exporter)
        remove_perm(obj_perms.manage_contacts_and_agents, self.user, exporter)
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self, exporter):
        self.user_export_app.exporter = exporter
        self.user_export_app.save()

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/add_exporter_office.html")
        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter-office"
        )

        assert response.context["fieldset_kwargs"] == {
            "legend": {
                "text": "What is the office address?",
                "classes": "govuk-fieldset__legend--l",
                "isPageHeading": True,
            }
        }

    def test_post(self, exporter):
        self.user_export_app.exporter = exporter
        self.user_export_app.save()

        # Test error message
        form_data = {
            "address_1": "",
            "address_2": "",
            "address_3": "",
            "address_4": "",
            "address_5": "",
            "postcode": "",
        }
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "address_1": ["Enter address 1"],
        }

        # Test post success
        form_data = {
            "address_1": "Test address_1",
            "address_2": "Test address_2",
            "address_3": "Test address_3",
            "address_4": "Test address_4",
            "address_5": "Test address_5",
            "postcode": "postcode",
        }
        previous_office_count = self.user_export_app.exporter.offices.count()

        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:exporter-office")

        assert self.user_export_app.exporter.offices.count() == previous_office_count + 1


class TestCreateExportApplicationExporterAgentOfficeCreateView:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        prototype_export_agent_client,
        prototype_export_agent_user,
        exporter,
        exporter_office,
        agent_exporter,
    ):
        self.user = prototype_export_agent_user
        self.url = reverse("ecil:export-application:exporter-agent-office-add")
        self.client = prototype_export_agent_client
        self.record = ECILUserExportApplication.objects.create(
            created_by=self.user,
            exporter=exporter,
            exporter_office=exporter_office,
            agent=agent_exporter,
        )

    def test_permission(self, ilb_admin_client, agent_exporter):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        # Requires edit access at organisation (so removing it should return forbidden)
        obj_perms = get_org_obj_permissions(agent_exporter)
        remove_perm(obj_perms.edit, self.user, agent_exporter)
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self, exporter):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/add_exporter_office.html")
        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter-agent-office"
        )

        assert response.context["fieldset_kwargs"] == {
            "legend": {
                "text": "What is the office address?",
                "classes": "govuk-fieldset__legend--l",
                "isPageHeading": True,
            }
        }

    def test_post(self, exporter):
        # Test error message
        form_data = {
            "address_1": "",
            "address_2": "",
            "address_3": "",
            "address_4": "",
            "address_5": "",
            "postcode": "",
        }
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "address_1": ["Enter address 1"],
        }

        # Test post success
        form_data = {
            "address_1": "Test address_1",
            "address_2": "Test address_2",
            "address_3": "Test address_3",
            "address_4": "Test address_4",
            "address_5": "Test address_5",
            "postcode": "postcode",
        }
        previous_office_count = self.record.agent.offices.count()

        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:exporter-agent-office")

        assert self.record.agent.offices.count() == previous_office_count + 1


class TestCreateExportApplicationAnotherExporterTemplateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:export-application:another-exporter")
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post_forbidden(self):
        response = self.client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/another_exporter.html")
        assert response.context["create_access_request_url"] == reverse("ecil:access_request:new")
        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter"
        )

    def test_get_agent_request(
        self, prototype_export_agent_user, prototype_export_agent_client, exporter, exporter_office
    ):
        # Setup record so the redirect is correct
        ECILUserExportApplication.objects.create(
            created_by=prototype_export_agent_user,
            exporter=exporter,
            exporter_office=exporter_office,
        )

        response = prototype_export_agent_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/another_exporter.html")
        assert response.context["create_access_request_url"] == reverse("ecil:access_request:new")
        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter-agent"
        )


class TestCreateExportApplicationAnotherExporterOfficeTemplateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:export-application:another-exporter-office")
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post_forbidden(self):
        response = self.client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/another_exporter_office.html")

        assert response.context["notification_banner_kwargs"] == {
            "text": "You need permission to add an address"
        }
        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter-office"
        )

    def test_get_agent_request(
        self,
        prototype_export_agent_user,
        prototype_export_agent_client,
        exporter,
        exporter_office,
        agent_exporter,
    ):
        # Setup record so the redirect is correct
        ECILUserExportApplication.objects.create(
            created_by=prototype_export_agent_user,
            exporter=exporter,
            exporter_office=exporter_office,
            agent=agent_exporter,
        )

        response = prototype_export_agent_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/another_exporter_office.html")

        assert response.context["notification_banner_kwargs"] == {
            "text": "You need permission to add an address"
        }

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:exporter-agent-office"
        )


class TestCreateExportApplicationAnotherContactTemplateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user):
        self.user = prototype_export_user
        self.url = reverse("ecil:export-application:another-contact")
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_post_forbidden(self):
        response = self.client.post(self.url)

        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_get(self, exporter_site, prototype_cfs_app_in_progress):
        referer_url = reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": exporter_site.pk}
        )
        headers = {"REFERER": f"http://{exporter_site.domain}{referer_url}"}
        response = self.client.get(self.url, headers=headers)

        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/another_contact.html")

        assert response.context["back_link_kwargs"] == {"text": "Back", "href": referer_url}


class TestExportApplicationAddExportCountryUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.user = prototype_export_user
        self.url = reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.app.pk}
        )
        self.client = prototype_export_client

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/export_countries.html")

        assert response.context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-cfs:application-contact",
            kwargs={"application_pk": self.app.pk},
        )

    def test_post(self):
        # Test error message
        form_data = {"countries": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "countries": ["Add a country or territory"],
        }

        invalid_country = (
            Country.util.get_all_countries().difference(Country.app.get_cfs_countries()).first()
        )
        form_data = {"countries": invalid_country.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "countries": [
                "Select a valid choice. That choice is not one of the available choices."
            ],
        }

        # Test post success
        valid_country = Country.app.get_cfs_countries().first()
        form_data = {"countries": valid_country.pk}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-application:countries-add-another", kwargs={"application_pk": self.app.pk}
        )

        self.app.refresh_from_db()

        assert self.app.countries.count() == 1
        assert self.app.countries.filter(pk=valid_country.pk).exists()


class TestExportApplicationAddAnotherExportCountryFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.user = prototype_export_user
        self.url = reverse(
            "ecil:export-application:countries-add-another", kwargs={"application_pk": self.app.pk}
        )
        self.client = prototype_export_client

    def test_permission(self, exporter_two_client):
        response = exporter_two_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/export_application/export_country_add_another.html")

        context = response.context
        assert context["back_link_kwargs"]["href"] == reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.app.pk}
        )

    def test_post(self):
        # Test error message
        form_data = {"add_another": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "add_another": ["Select yes or no"],
        }

        # Test post success (yes)
        form_data = {"add_another": YesNoChoices.yes}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.app.pk}
        )

        # Test post success (no)
        form_data = {"add_another": YesNoChoices.no}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-cfs:schedule-create", kwargs={"application_pk": self.app.pk}
        )


class TestExportApplicationConfirmRemoveCountryFormView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.valid_country = Country.app.get_cfs_countries().first()
        self.app = prototype_cfs_app_in_progress
        self.user = prototype_export_user
        self.url = reverse(
            "ecil:export-application:countries-remove",
            kwargs={"application_pk": self.app.pk, "country_pk": self.valid_country.pk},
        )
        self.client = prototype_export_client
        self.app.countries.add(self.valid_country)

    def test_permission(self, ilb_admin_client):
        response = ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_get(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assertTemplateUsed(response, "ecil/gds_form.html")
        assertInHTML(
            f"Are you sure you want to remove {self.valid_country.name}?",
            response.content.decode("utf-8"),
        )

    def test_post(self):
        # Test error message
        form_data = {"are_you_sure": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "are_you_sure": ["Select yes or no"],
        }

        self.app.countries.add(Country.app.get_cfs_countries().last())
        assert self.app.countries.count() == 2

        # Test post success
        form_data = {"are_you_sure": YesNoChoices.yes}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-application:countries-add-another", kwargs={"application_pk": self.app.pk}
        )

        self.app.refresh_from_db()
        assert self.app.countries.count() == 1

        # Test removing last country redirects to correct view.
        url = reverse(
            "ecil:export-application:countries-remove",
            kwargs={
                "application_pk": self.app.pk,
                "country_pk": Country.app.get_cfs_countries().last().pk,
            },
        )
        form_data = {"are_you_sure": YesNoChoices.yes}
        response = self.client.post(url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.app.pk}
        )

        self.app.refresh_from_db()
        assert self.app.countries.count() == 0
