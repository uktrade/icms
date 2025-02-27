from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed


class TestAnotherExportApplicationContactTemplateView:
    @pytest.fixture(autouse=True)
    def setup(self, prototype_client, prototype_user):
        self.user = prototype_user
        self.url = reverse("ecil:export-application:another-contact")
        self.client = prototype_client

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
