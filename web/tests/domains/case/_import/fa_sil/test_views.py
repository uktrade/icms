from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.models import ImportApplicationLicence, SILApplication, Task
from web.tests.application_utils import create_import_app, save_app_data

if TYPE_CHECKING:
    from django.test.client import Client


def test_create_fa_sil(importer_client, importer, office):
    app_pk = create_import_app(
        client=importer_client,
        view_name="import:create-fa-sil",
        importer_pk=importer.pk,
        office_pk=office.pk,
    )

    app = SILApplication.objects.get(pk=app_pk)
    case_progress.check_expected_task(app, Task.TaskType.PREPARE)
    case_progress.check_expected_status(app, [ImpExpStatus.IN_PROGRESS])


class TestEditFirearmsSILApplication:
    client: "Client"
    app: SILApplication

    @pytest.fixture(autouse=True)
    def set_client(self, importer_client):
        self.client = importer_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, importer, office):
        app_pk = create_import_app(
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

    def test_add_section_1_goods(self):
        add_goods_url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": self.app.pk, "sil_section_type": "section1"},
        )

        # Unlimited quantity

        data = {
            "manufacture": False,
            "description": "sec 1 goods",
            "quantity": "",
            "unlimited_quantity": "on",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == 302

        # Specified quantity

        data = {
            "manufacture": False,
            "description": "More sec 1 goods",
            "quantity": 10,
            "unlimited_quantity": "off",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == 302

        # Invalid quantity data

        data = {
            "manufacture": True,
            "description": "Invalid Sec 1 goods",
            "quantity": "",
            "unlimited_quantity": "",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == 200
        assertInHTML(
            '<div class="error-message">You must enter either a quantity or select unlimited quantity</div>',
            response.content.decode("utf-8"),
        )

        self.app.refresh_from_db()
        assert self.app.goods_section1.count() == 2

    def test_add_section_2_goods(self):
        add_goods_url = reverse(
            "import:fa-sil:add-section",
            kwargs={"application_pk": self.app.pk, "sil_section_type": "section2"},
        )

        # Unlimited quantity

        data = {
            "manufacture": False,
            "description": "sec 2 goods",
            "quantity": "",
            "unlimited_quantity": "on",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == 302

        # Specified quantity

        data = {
            "manufacture": False,
            "description": "More sec 2 goods",
            "quantity": 20,
            "unlimited_quantity": "off",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == 302

        # Invalid quantity data

        data = {
            "manufacture": False,
            "description": "Invalid Sec 2 goods",
            "quantity": "",
            "unlimited_quantity": "",
        }
        response = self.client.post(add_goods_url, data=data)
        assert response.status_code == 200
        assertInHTML(
            '<div class="error-message">You must enter either a quantity or select unlimited quantity</div>',
            response.content.decode("utf-8"),
        )

        self.app.refresh_from_db()
        assert self.app.goods_section2.count() == 2

    def test_validate_query_param_shows_errors(self):
        edit_url = reverse("import:fa-sil:edit", kwargs={"application_pk": self.app.pk})

        # No query param so no errors by default
        response = self.client.get(f"{edit_url}")
        assert response.status_code == 200
        form = response.context["form"]
        assert not form.errors

        # Validate every field to check for any errors
        response = self.client.get(f"{edit_url}?validate")
        assert response.status_code == 200
        form = response.context["form"]
        message = form.errors["origin_country"][0]
        assert message == "You must enter this item"


def test_fa_sil_app_submitted_has_a_licence(fa_sil_app_submitted):
    assert fa_sil_app_submitted.licences.filter(
        status=ImportApplicationLicence.Status.DRAFT
    ).exists()
