from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from web.ecil.gds.forms import fields


class TestCFSApplicationReferenceUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.url = reverse(
            "ecil:export-cfs:application-reference", kwargs={"application_pk": self.app.pk}
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
        assertTemplateUsed(response, "ecil/gds_form.html")

        assert response.context["back_link_kwargs"] == {
            "text": "Back",
            "href": reverse("workbasket"),
        }

    def test_post(self):
        # Test optional is valid
        form_data = {"applicant_reference": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": self.app.pk}
        )

        # Test post success
        form_data = {"applicant_reference": "test-application-reference"}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": self.app.pk}
        )

        self.app.refresh_from_db()
        assert self.app.applicant_reference == "test-application-reference"


class TestCFSApplicationContactUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.user = prototype_export_user
        self.url = reverse(
            "ecil:export-cfs:application-contact", kwargs={"application_pk": self.app.pk}
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
        assertTemplateUsed(response, "ecil/gds_form.html")

        assert response.context["back_link_kwargs"] == {
            "text": "Back",
            "href": reverse(
                "ecil:export-cfs:application-reference", kwargs={"application_pk": self.app.pk}
            ),
        }

    def test_post(self):
        # Test error message
        form_data = {"contact": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "contact": ["Select the main contact for your application"],
        }

        # Test post success when picking user
        form_data = {"contact": str(self.user.pk)}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "ecil:export-application:countries", kwargs={"application_pk": self.app.pk}
        )

        self.app.refresh_from_db()
        assert self.app.contact == self.user

        # Test post success when picking "Someone else"
        form_data = {"contact": fields.GovUKRadioInputField.NONE_OF_THESE}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("ecil:export-application:another-contact")

        self.app.refresh_from_db()
        assert self.app.contact is None


class TestCFSScheduleCreateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_export_client, prototype_export_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.url = reverse(
            "ecil:export-cfs:schedule-create", kwargs={"application_pk": self.app.pk}
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
        assertTemplateUsed(response, "ecil/cfs/schedule_create.html")

        assert response.context["back_link_kwargs"] == {
            "text": "Back",
            "href": reverse(
                "ecil:export-application:countries", kwargs={"application_pk": self.app.pk}
            ),
        }

        assert response.context["create_schedule_btn_kwargs"] == {
            "text": "Create a product schedule",
            "type": "submit",
            "isStartButton": True,
            "preventDoubleClick": True,
        }

    def test_post(self):
        assert self.app.schedules.count() == 1

        # Test post success
        response = self.client.post(self.url)

        self.app.refresh_from_db()
        assert self.app.schedules.count() == 2

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse(
            "export:cfs-schedule-edit",
            kwargs={
                "application_pk": self.app.pk,
                "schedule_pk": self.app.schedules.last().pk,
            },
        )
