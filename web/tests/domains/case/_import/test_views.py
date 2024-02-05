from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertRedirects

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.models import (
    ICMSHMRCChiefRequest,
    ImportApplicationType,
    SILApplication,
    Task,
    VariationRequest,
    WoodQuotaApplication,
)
from web.tests.auth import AuthTestCase
from web.tests.helpers import SearchURLS

from . import factory


@pytest.mark.django_db
def test_preview_cover_letter(
    ilb_admin_user, ilb_admin_client, importer_one_contact, importer, office
):
    ilb_admin = ilb_admin_user
    user = importer_one_contact

    process = factory.OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        created_by=user,
        last_updated_by=user,
        case_owner=ilb_admin,
        importer_office=office,
    )
    Task.objects.create(process=process, task_type=Task.TaskType.PROCESS)
    oil_app = process.get_specific_model()
    oil_app.licences.create()

    url = reverse(
        "case:cover-letter-preview", kwargs={"application_pk": process.pk, "case_type": "import"}
    )
    response = ilb_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=CoverLetter-Preview.pdf"

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 5000 < len(pdf) < 15000


@pytest.mark.django_db
@patch("web.domains.signature.utils.get_signature_file_base64")
def test_preview_licence(
    mock_file, ilb_admin_user, ilb_admin_client, importer_one_contact, importer, office
):
    mock_file.return_value = ""
    ilb_admin = ilb_admin_user
    user = importer_one_contact

    process = factory.OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        importer_office=office,
        created_by=user,
        last_updated_by=user,
        case_owner=ilb_admin,
    )
    Task.objects.create(process=process, task_type=Task.TaskType.PROCESS)
    oil_app = process.get_specific_model()
    oil_app.licences.create()

    url = reverse(
        "case:licence-preview", kwargs={"application_pk": process.pk, "case_type": "import"}
    )
    response = ilb_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=Licence-Preview.pdf"

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 10000 < len(pdf) < 20000


@pytest.mark.django_db
def test_preview_cfs_certificate(ilb_admin_client, cfs_app_submitted):
    process = cfs_app_submitted
    country = process.countries.first()

    url = reverse(
        "case:certificate-preview",
        kwargs={"application_pk": process.pk, "case_type": "import", "country_pk": country.pk},
    )
    response = ilb_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=Certificate-Preview.pdf"

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 5000 < len(pdf) < 15000


@pytest.mark.django_db
def test_preview_com_certificate(ilb_admin_client, com_app_submitted):
    process = com_app_submitted
    country = process.countries.first()

    url = reverse(
        "case:certificate-preview",
        kwargs={"application_pk": process.pk, "case_type": "import", "country_pk": country.pk},
    )
    response = ilb_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=Certificate-Preview.pdf"

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 5000 < len(pdf) < 15000


@pytest.mark.django_db
def test_preview_gmp_certificate(ilb_admin_client, gmp_app_submitted):
    process = gmp_app_submitted
    country = process.countries.first()

    url = reverse(
        "case:certificate-preview",
        kwargs={"application_pk": process.pk, "case_type": "import", "country_pk": country.pk},
    )
    response = ilb_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=Certificate-Preview.pdf"

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 5000 < len(pdf) < 15000


class TestBypassChiefView:
    client: "Client"
    wood_app: WoodQuotaApplication

    @pytest.fixture(autouse=True)
    def set_client(self, ilb_admin_client):
        self.client = ilb_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, wood_app_submitted):
        """using the submitted app override the app to the state we want."""
        wood_app_submitted.status = ImpExpStatus.PROCESSING
        wood_app_submitted.save()

        task = wood_app_submitted.tasks.get(is_active=True)
        task.is_active = False
        task.finished = timezone.now()
        task.save()

        Task.objects.create(
            process=wood_app_submitted, task_type=Task.TaskType.CHIEF_WAIT, previous=task
        )

        self.wood_app = wood_app_submitted
        ICMSHMRCChiefRequest.objects.create(
            import_application=self.wood_app,
            case_reference=self.wood_app.reference,
            request_data={"foo": "bar"},
            request_sent_datetime=timezone.now(),
        )

    def test_bypass_chief_success(self):
        url = reverse(
            "import:bypass-chief",
            kwargs={"application_pk": self.wood_app.pk, "chief_status": "success"},
        )
        resp = self.client.post(url)

        assertRedirects(resp, reverse("workbasket"), 302)

        self.wood_app.refresh_from_db()

        case_progress.check_expected_status(self.wood_app, [ImpExpStatus.COMPLETED])
        assert case_progress.get_active_task_list(self.wood_app) == []

    def test_bypass_chief_failure(self):
        url = reverse(
            "import:bypass-chief",
            kwargs={"application_pk": self.wood_app.pk, "chief_status": "failure"},
        )
        resp = self.client.post(url)

        assertRedirects(resp, reverse("workbasket"), 302)

        self.wood_app.refresh_from_db()

        case_progress.check_expected_status(self.wood_app, [ImpExpStatus.PROCESSING])
        case_progress.check_expected_task(self.wood_app, Task.TaskType.CHIEF_ERROR)

    def test_bypass_chief_variation_request_success(self, ilb_admin_user):
        self.wood_app.status = ImpExpStatus.VARIATION_REQUESTED
        self.wood_app.variation_requests.create(
            status=VariationRequest.Statuses.OPEN,
            what_varied="Dummy what_varied",
            why_varied="Dummy why_varied",
            when_varied=timezone.now().date(),
            requested_by=ilb_admin_user,
        )

        self.wood_app.save()

        url = reverse(
            "import:bypass-chief",
            kwargs={"application_pk": self.wood_app.pk, "chief_status": "success"},
        )
        resp = self.client.post(url)

        assertRedirects(resp, reverse("workbasket"), 302)

        self.wood_app.refresh_from_db()

        case_progress.check_expected_status(self.wood_app, [ImpExpStatus.COMPLETED])
        assert case_progress.get_active_task_list(self.wood_app) == []

        vr = self.wood_app.variation_requests.first()
        assert vr.status == VariationRequest.Statuses.ACCEPTED


class TestBypassChiefViewRevokeLicence:
    client: Client
    app: SILApplication
    success_url: str
    fail_url: str

    @pytest.fixture(autouse=True)
    def setup(self, ilb_admin_client, completed_sil_app):
        self.client = ilb_admin_client
        self.app = completed_sil_app
        self.success_url = reverse(
            "import:bypass-chief", kwargs={"application_pk": self.app.pk, "chief_status": "success"}
        )
        self.fail_url = reverse(
            "import:bypass-chief", kwargs={"application_pk": self.app.pk, "chief_status": "failure"}
        )

        revoke_url = SearchURLS.revoke_licence(self.app.pk)
        self.client.post(revoke_url, data={"reason": "test_reason"})
        self.app.refresh_from_db()

    def test_permission(self, importer_client, exporter_client):
        # Post only view.
        response = self.client.post(self.success_url)
        assert response.status_code == HTTPStatus.FOUND

        response = importer_client.post(self.success_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = exporter_client.post(self.success_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_bypass_chief_revoke_licence_success(self):
        case_progress.check_expected_status(self.app, [ImpExpStatus.REVOKED])
        case_progress.check_expected_task(self.app, Task.TaskType.CHIEF_REVOKE_WAIT)

        self.client.post(self.success_url)

        # The CHIEF_REVOKE_WAIT should have been ended
        case_progress.check_expected_status(self.app, [ImpExpStatus.REVOKED])
        assert case_progress.get_active_tasks(self.app, select_for_update=False).count() == 0

    def test_bypass_chief_revoke_licence_failure(self):
        case_progress.check_expected_status(self.app, [ImpExpStatus.REVOKED])
        case_progress.check_expected_task(self.app, Task.TaskType.CHIEF_REVOKE_WAIT)

        self.client.post(self.fail_url)

        case_progress.check_expected_status(self.app, [ImpExpStatus.REVOKED])
        case_progress.check_expected_task(self.app, Task.TaskType.CHIEF_ERROR)


class TestApplicationChoice(AuthTestCase):
    url = reverse("import:choose")

    def test_create_no_access(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == 200

    def test_create_has_access(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == 403

    def test_show_only_active_application_choices(self):
        new_application_type_name = "NEW APPLICATION TYPE"

        application_type = ImportApplicationType.objects.create(
            type=ImportApplicationType.Types.OPT,
            sub_type=ImportApplicationType.SubTypes.DFL,
            name=new_application_type_name,
            is_active=True,
            sigl_flag=False,
            chief_flag=False,
            paper_licence_flag=False,
            electronic_licence_flag=False,
            cover_letter_flag=False,
            cover_letter_schedule_flag=False,
            category_flag=False,
            quantity_unlimited_flag=False,
            exp_cert_upload_flag=False,
            supporting_docs_upload_flag=False,
            multiple_commodities_flag=False,
            usage_auto_category_desc_flag=False,
            case_checklist_flag=False,
            importer_printable=False,
            declaration_template_id=1,
        )

        response = self.importer_client.get(self.url)
        assert new_application_type_name in response.content.decode()

        application_type.is_active = False
        application_type.save()

        response = self.importer_client.get(self.url)
        assert new_application_type_name not in response.content.decode()
