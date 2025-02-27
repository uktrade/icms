from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed


class TestCFSApplicationReferenceUpdateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client, prototype_user, prototype_cfs_app_in_progress):
        self.app = prototype_cfs_app_in_progress
        self.user = prototype_user
        self.url = reverse(
            "ecil:export-cfs:application-reference", kwargs={"application_pk": self.app.pk}
        )
        self.client = prototype_client

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
        # Test error message
        form_data = {"applicant_reference": ""}
        response = self.client.post(self.url, data=form_data)
        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]
        assert form.errors == {
            "applicant_reference": ["Enter a name for the application"],
        }

        # Test post success
        form_data = {"applicant_reference": "test-application-reference"}
        response = self.client.post(self.url, data=form_data)

        assert response.status_code == HTTPStatus.FOUND
        assert response.url == reverse("workbasket")

        self.app.refresh_from_db()
        assert self.app.applicant_reference == "test-application-reference"
