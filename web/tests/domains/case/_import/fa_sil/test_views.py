from typing import TYPE_CHECKING

import pytest
from django.urls import reverse

from web.domains.case._import.fa_sil.models import SILApplication
from web.domains.case.shared import ImpExpStatus
from web.flow.models import Task
from web.tests.application_utils import create_app, save_app_data

if TYPE_CHECKING:
    from django.test.client import Client


def test_create_fa_sil(importer_client, importer, office):
    app_pk = create_app(
        client=importer_client,
        view_name="import:create-fa-sil",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )

    app = SILApplication.objects.get(pk=app_pk)
    app.get_expected_task(Task.TaskType.PREPARE)
    app.check_expected_status(ImpExpStatus.IN_PROGRESS)


class TestEditFirearmsSILApplication:
    client: "Client"
    app: SILApplication

    @pytest.fixture(autouse=True)
    def set_client(self, importer_client):
        self.client = importer_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, importer, office):
        app_pk = create_app(
            client=self.client,
            view_name="import:create-fa-sil",
            importer_pk=importer.pk,
            office_pk=office.pk,
        )
        self.app = SILApplication.objects.get(pk=app_pk)

    def test_can_edit_application(self):
        # Test we can save a single field now
        save_app_data(
            client=self.client,
            view_name="import:fa-sil:edit",
            app_pk=self.app.pk,
            form_data={"applicant_reference": "A new value"},
        )

        self.app.refresh_from_db()
        assert self.app.applicant_reference == "A new value"

    def test_validate_query_param_shows_errors(self):
        edit_url = reverse("import:fa-sil:edit", kwargs={"application_pk": self.app.pk})

        # No query param so no errors by default
        response = self.client.get(f"{edit_url}")
        assert response.status_code == 200
        form = response.context["form"]
        assert not form.errors

        # Validate every field to check for any errors
        response = self.client.get(f"{edit_url}?validate=1")
        assert response.status_code == 200
        form = response.context["form"]
        message = form.errors["origin_country"][0]
        assert message == "You must enter this item"
