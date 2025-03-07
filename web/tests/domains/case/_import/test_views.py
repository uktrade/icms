import datetime as dt
from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertRedirects

from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.forms.fields import JQUERY_DATE_FORMAT
from web.models import (
    Country,
    ICMSHMRCChiefRequest,
    ImportApplicationType,
    SILApplication,
    Task,
    Template,
    VariationRequest,
    WoodQuotaApplication,
)
from web.tests.auth import AuthTestCase
from web.tests.helpers import CaseURLS, SearchURLS, add_variation_request_to_app

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

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 5000 < len(pdf) < 150000


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

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 10000 < len(pdf) < 150000


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

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 5000 < len(pdf)


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

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 5000 < len(pdf) < 150000


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

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 5000 < len(pdf) < 200000


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
            type=ImportApplicationType.Types.WOOD_QUOTA,
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


class TestIMICaseListView(AuthTestCase):
    url = reverse("import:imi-case-list")

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_valid_record(self, completed_sil_app):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        # Sil app doesn't show because it has the wrong cc
        assert len(response.context["imi_list"]) == 0

        # Set consignment_country to a valid country
        completed_sil_app.consignment_country = Country.util.get_eu_countries().first()
        completed_sil_app.save()

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert len(response.context["imi_list"]) == 1
        imi_app = response.context["imi_list"][0]

        assert imi_app.reference == completed_sil_app.reference

    def test_submit_after_2024(self, completed_sil_app):
        # Set consignment_country to a valid country
        completed_sil_app.consignment_country = Country.util.get_eu_countries().first()
        # a 2023 submit datetime should not show
        completed_sil_app.submit_datetime = dt.datetime(2023, 12, 31, 23, 59, 59, tzinfo=dt.UTC)

        completed_sil_app.save()

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert len(response.context["imi_list"]) == 0

        # Change the submit date to 2024
        completed_sil_app.submit_datetime = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
        completed_sil_app.save()

        # Check record now shows.
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        assert len(response.context["imi_list"]) == 1
        imi_app = response.context["imi_list"][0]

        assert imi_app.reference == completed_sil_app.reference


class TestGetEndorsementTextView(AuthTestCase):
    url = reverse("import:get-endorsement-text")

    @pytest.fixture(autouse=True)
    def setup(self, _setup):
        self.endorsement = Template.objects.filter(template_type=Template.ENDORSEMENT).first()
        self.url = reverse("import:get-endorsement-text") + f"?template_pk={self.endorsement.pk}"

    def test_permission(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_only(self):
        response = self.ilb_admin_client.post(self.url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_get_endorsement_text(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assert response.json() == {"text": self.endorsement.template_content}

    def test_invalid_template_error(self):
        url = reverse("import:get-endorsement-text") + "?template_pk=-111"
        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.json() == {}


class TestILBEditImportLicence(AuthTestCase):
    def test_submitted_app(self, fa_dfl_app_submitted):
        app = fa_dfl_app_submitted
        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk))

        # Create all three errors with all past end dates and set the wrong way around
        past_start_date = dt.date(dt.date.today().year - 1, 1, 1)
        past_end_date = dt.date(dt.date.today().year - 1, 1, 2)

        form_data = {
            "licence_start_date": past_end_date.strftime(JQUERY_DATE_FORMAT),
            "licence_end_date": past_start_date.strftime(JQUERY_DATE_FORMAT),
            "issue_paper_licence_only": False,
        }
        response = self.ilb_admin_client.post(CaseURLS.edit_import_licence(app.pk), form_data)

        assert response.status_code == HTTPStatus.OK
        form = response.context["form"]

        assert len(form.errors) == 2
        assert form.errors["licence_start_date"][0] == "Date must be in the future."
        assert form.errors["licence_end_date"][0] == "Date must be in the future."
        assert form.errors["licence_end_date"][1] == "End Date must be after Start Date."

    def test_variation_request(self, completed_dfl_app):
        #
        # Setup
        app = completed_dfl_app

        pack = document_pack.pack_draft_create(app, variation_request=True)
        add_variation_request_to_app(
            app, self.ilb_admin_user, status=VariationRequest.Statuses.OPEN
        )
        app.status = ImpExpStatus.VARIATION_REQUESTED
        app.save()

        Task.objects.create(process=app, task_type=Task.TaskType.PROCESS, previous=None)
        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, case_type="import"))

        #
        # Test
        start_date = pack.licence_start_date
        future_end_date = dt.date(dt.date.today().year + 1, 1, 1)

        form_data = {
            "licence_start_date": start_date.strftime(JQUERY_DATE_FORMAT),
            "licence_end_date": future_end_date.strftime(JQUERY_DATE_FORMAT),
            "issue_paper_licence_only": False,
        }
        response = self.ilb_admin_client.post(CaseURLS.edit_import_licence(app.pk), form_data)

        #
        # Assert
        assert response.status_code == HTTPStatus.FOUND
        app.refresh_from_db()
        pack.refresh_from_db()
        assert pack.licence_start_date == start_date
        assert pack.licence_end_date == future_end_date
