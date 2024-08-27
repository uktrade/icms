import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from web.domains.case.models import DocumentPackBase
from web.domains.case.services import case_progress, document_pack
from web.domains.case.shared import ImpExpStatus
from web.forms.fields import JQUERY_DATE_FORMAT
from web.mail.constants import EmailTypes
from web.mail.url_helpers import get_case_view_url, get_validate_digital_signatures_url
from web.models import Task, VariationRequest
from web.sites import SiteName, get_caseworker_site_domain, get_importer_site_domain
from web.tests.helpers import (
    CaseURLS,
    add_variation_request_to_app,
    check_gov_notify_email_was_sent,
)


class TestVariationRequestManageView:
    @pytest.fixture(autouse=True)
    def set_client(self, ilb_admin_client):
        self.client = ilb_admin_client

    def test_get_variations_for_import_application(self, ilb_admin_user, wood_app_submitted):
        wood_app = wood_app_submitted
        self.client.post(CaseURLS.take_ownership(wood_app.pk))

        # Add a few previous variation requests
        add_variation_request_to_app(
            wood_app, ilb_admin_user, status=VariationRequest.Statuses.REJECTED
        )
        add_variation_request_to_app(
            wood_app, ilb_admin_user, status=VariationRequest.Statuses.ACCEPTED
        )
        # Add an open one last (as it's the latest)
        add_variation_request_to_app(
            wood_app, ilb_admin_user, status=VariationRequest.Statuses.OPEN
        )

        response = self.client.get(CaseURLS.manage_variations(wood_app.pk))

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/case/manage/variations/import/manage.html")

        cd = response.context_data
        vrs = cd["variation_requests"]

        expected_status_order = [
            VariationRequest.Statuses.OPEN,
            VariationRequest.Statuses.ACCEPTED,
            VariationRequest.Statuses.REJECTED,
        ]

        assert expected_status_order == [vr.status for vr in vrs]

    def test_get_variations_for_export_application(self, ilb_admin_user, com_app_submitted):
        com_app = com_app_submitted

        self.client.post(CaseURLS.take_ownership(com_app.pk))

        # Add a few previous variation requests
        add_variation_request_to_app(
            com_app, ilb_admin_user, status=VariationRequest.Statuses.CANCELLED
        )
        add_variation_request_to_app(
            com_app, ilb_admin_user, status=VariationRequest.Statuses.CLOSED
        )
        # Add an open one last (as it's the latest)
        add_variation_request_to_app(com_app, ilb_admin_user, status=VariationRequest.Statuses.OPEN)

        response = self.client.get(CaseURLS.manage_variations(com_app.pk, case_type="export"))

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/case/manage/variations/export/manage.html")

        cd = response.context_data
        vrs = cd["variation_requests"]

        expected_status_order = [
            VariationRequest.Statuses.OPEN,
            VariationRequest.Statuses.CLOSED,
            VariationRequest.Statuses.CANCELLED,
        ]

        assert expected_status_order == [vr.status for vr in vrs]


class TestVariationRequestCancelView:
    @pytest.fixture(autouse=True)
    def set_client(self, ilb_admin_client):
        self.client = ilb_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, wood_app_submitted, importer_one_contact):
        self.wood_app = wood_app_submitted
        self.client.post(CaseURLS.take_ownership(self.wood_app.pk))

        self.wood_app.refresh_from_db()
        self.wood_app.status = ImpExpStatus.VARIATION_REQUESTED
        add_variation_request_to_app(self.wood_app, importer_one_contact)
        self.wood_app.save()

        # Set the draft licence active and create a second one
        document_pack.pack_draft_set_active(self.wood_app)
        self.active_licence = document_pack.pack_active_get(self.wood_app)
        self.draft_licence = self.wood_app.licences.create()

    def test_cancel_variation_request_get(self):
        vr = self.wood_app.variation_requests.first()
        resp = self.client.get(CaseURLS.cancel_variation_request(self.wood_app.pk, vr.pk))

        cd = resp.context_data

        assert resp.status_code == 200
        assert cd["object"] == vr
        assert cd["process"] == self.wood_app
        assert cd["page_title"] == f"Variations {self.wood_app.get_reference()}"
        assert cd["case_type"] == "import"

    def test_cancel_variation_request_post(self, ilb_admin_user):
        vr = self.wood_app.variation_requests.first()
        resp = self.client.post(
            CaseURLS.cancel_variation_request(self.wood_app.pk, vr.pk),
            {"reject_cancellation_reason": "Test cancellation reason"},
        )

        assertRedirects(resp, reverse("workbasket"), 302)

        self.wood_app.refresh_from_db()
        vr.refresh_from_db()

        assert vr.status == VariationRequest.Statuses.CANCELLED
        assert vr.reject_cancellation_reason == "Test cancellation reason"
        assert vr.closed_by == ilb_admin_user
        assert vr.closed_datetime.date() == timezone.now().date()

        case_progress.check_expected_status(self.wood_app, [ImpExpStatus.COMPLETED])
        assert case_progress.get_active_task_list(self.wood_app) == []

        self.active_licence.refresh_from_db()
        assert self.active_licence.status == DocumentPackBase.Status.ACTIVE

        # Archived now the variation has been cancelled.
        self.draft_licence.refresh_from_db()
        assert self.draft_licence.status == DocumentPackBase.Status.ARCHIVED
        check_gov_notify_email_was_sent(
            1,
            ["I1_main_contact@example.com"],  # /PS-IGNORE
            EmailTypes.APPLICATION_VARIATION_REQUEST_CANCELLED,
            {
                "reference": self.wood_app.reference,
                "validate_digital_signatures_url": get_validate_digital_signatures_url(
                    get_importer_site_domain()
                ),
                "application_url": get_case_view_url(self.wood_app, get_importer_site_domain()),
                "reason": "Test cancellation reason",
                "icms_url": get_importer_site_domain(),
                "service_name": SiteName.IMPORTER.label,
            },
        )


class TestVariationRequestCancelViewForExportApplication:
    @pytest.fixture(autouse=True)
    def set_client(self, ilb_admin_client):
        self.client = ilb_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, com_app_submitted, ilb_admin_user):
        self.app = com_app_submitted
        self.client.post(CaseURLS.take_ownership(self.app.pk))

        self.app.refresh_from_db()
        self.app.status = ImpExpStatus.VARIATION_REQUESTED
        add_variation_request_to_app(
            self.app, ilb_admin_user, status=VariationRequest.Statuses.OPEN
        )
        self.app.save()

        # Set the draft licence active and create a second one
        document_pack.pack_draft_set_active(self.app)
        self.active_certificate = document_pack.pack_active_get(self.app)
        self.draft_certificate = self.app.certificates.create()

    def test_cancel_variation_request_post(self, ilb_admin_user):
        vr = self.app.variation_requests.first()
        resp = self.client.post(
            CaseURLS.cancel_variation_request(self.app.pk, vr.pk, case_type="export")
        )

        assertRedirects(resp, reverse("workbasket"), 302)

        self.app.refresh_from_db()
        vr.refresh_from_db()

        assert vr.status == VariationRequest.Statuses.CANCELLED
        assert vr.closed_by == ilb_admin_user
        assert vr.closed_datetime.date() == timezone.now().date()

        case_progress.check_expected_status(self.app, [ImpExpStatus.COMPLETED])
        assert case_progress.get_active_task_list(self.app) == []

        self.active_certificate.refresh_from_db()
        assert self.active_certificate.status == DocumentPackBase.Status.ACTIVE

        # Archived now the variation has been cancelled.
        self.draft_certificate.refresh_from_db()
        assert self.draft_certificate.status == DocumentPackBase.Status.ARCHIVED
        check_gov_notify_email_was_sent(
            1,
            ["ilb_admin_user@example.com"],  # /PS-IGNORE
            EmailTypes.APPLICATION_VARIATION_REQUEST_CANCELLED,
            {
                "reference": self.app.reference,
                "validate_digital_signatures_url": get_validate_digital_signatures_url(
                    get_caseworker_site_domain()
                ),
                "application_url": get_case_view_url(self.app, get_caseworker_site_domain()),
                "reason": None,
                "icms_url": get_caseworker_site_domain(),
                "service_name": SiteName.CASEWORKER.label,
            },
        )


class TestVariationRequestRequestUpdateView:
    @pytest.fixture(autouse=True)
    def set_client(self, ilb_admin_client):
        self.client = ilb_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, wood_app_submitted, importer_one_contact):
        self.wood_app = wood_app_submitted
        self.client.post(CaseURLS.take_ownership(self.wood_app.pk))

        self.wood_app.refresh_from_db()
        self.wood_app.status = ImpExpStatus.VARIATION_REQUESTED
        self.wood_app.save()

        add_variation_request_to_app(
            self.wood_app, importer_one_contact, status=VariationRequest.Statuses.OPEN
        )
        self.vr = self.wood_app.variation_requests.get(status=VariationRequest.Statuses.OPEN)

    def test_request_update_post(self):
        response = self.client.post(
            CaseURLS.variation_request_request_update(self.wood_app.pk, self.vr.pk),
            {"update_request_reason": "Dummy update request reason"},
        )

        redirect_url = CaseURLS.manage_variations(self.wood_app.pk)
        assertRedirects(response, redirect_url, 302)

        # Check the status is the same but the app has a new task
        self.wood_app.refresh_from_db()
        case_progress.check_expected_status(self.wood_app, [ImpExpStatus.VARIATION_REQUESTED])
        case_progress.check_expected_task(self.wood_app, Task.TaskType.VR_REQUEST_CHANGE)

        # Check the reason has been saved
        self.vr.refresh_from_db()
        assert self.vr.update_request_reason == "Dummy update request reason"
        check_gov_notify_email_was_sent(
            1,
            ["I1_main_contact@example.com"],  # /PS-IGNORE
            EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED,
            {
                "reference": self.wood_app.reference,
                "validate_digital_signatures_url": get_validate_digital_signatures_url(
                    get_importer_site_domain()
                ),
                "application_url": get_case_view_url(self.wood_app, get_importer_site_domain()),
                "reason": "Dummy update request reason",
                "icms_url": get_importer_site_domain(),
                "service_name": SiteName.IMPORTER.label,
            },
        )


class TestVariationRequestCancelUpdateRequestView:
    @pytest.fixture(autouse=True)
    def set_client(self, ilb_admin_client):
        self.client = ilb_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, wood_app_submitted, importer_one_contact):
        self.app = wood_app_submitted
        self.client.post(CaseURLS.take_ownership(self.app.pk))

        self.app.refresh_from_db()
        self.app.status = ImpExpStatus.VARIATION_REQUESTED
        self.app.save()

        add_variation_request_to_app(
            self.app, importer_one_contact, status=VariationRequest.Statuses.OPEN
        )
        self.vr = self.app.variation_requests.get(status=VariationRequest.Statuses.OPEN)

        self.client.post(
            CaseURLS.variation_request_request_update(self.app.pk, self.vr.pk),
            {"update_request_reason": "Dummy update request reason"},
        )
        check_gov_notify_email_was_sent(
            1,
            ["I1_main_contact@example.com"],  # /PS-IGNORE
            EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED,
            {
                "reference": self.app.reference,
                "validate_digital_signatures_url": get_validate_digital_signatures_url(
                    get_importer_site_domain()
                ),
                "application_url": get_case_view_url(self.app, get_importer_site_domain()),
                "reason": "Dummy update request reason",
                "icms_url": get_importer_site_domain(),
                "service_name": SiteName.IMPORTER.label,
            },
        )
        mail.outbox = []

    @pytest.fixture(autouse=True)
    def set_url(self, set_app):
        self.url = CaseURLS.variation_request_cancel_update_request(self.app.pk, self.vr.pk)

    def test_get_not_allowed(self):
        response = self.client.get(self.url)

        assert response.status_code == 405

    def test_importer_client_forbidden(self, importer_client):
        response = importer_client.post(self.url)

        assert response.status_code == 403

    def test_post_successful(self):
        response = self.client.post(self.url)

        redirect_url = CaseURLS.manage_variations(self.app.pk)
        assertRedirects(response, redirect_url, 302)

        self.app.refresh_from_db()
        self.vr.refresh_from_db()

        case_progress.check_expected_status(self.app, [ImpExpStatus.VARIATION_REQUESTED])
        assert Task.TaskType.VR_REQUEST_CHANGE not in case_progress.get_active_task_list(self.app)

        assert self.vr.update_request_reason is None

        check_gov_notify_email_was_sent(
            1,
            ["I1_main_contact@example.com"],  # /PS-IGNORE
            EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_CANCELLED,
            {
                "reference": self.app.reference,
                "validate_digital_signatures_url": get_validate_digital_signatures_url(
                    get_importer_site_domain()
                ),
                "application_url": get_case_view_url(self.app, get_importer_site_domain()),
                "icms_url": get_importer_site_domain(),
                "service_name": SiteName.IMPORTER.label,
            },
        )


class TestVariationRequestRespondToUpdateRequestView:
    @pytest.fixture(autouse=True)
    def set_client(self, importer_client, ilb_admin_client):
        self.client = importer_client
        self.admin_client = ilb_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, wood_app_submitted, importer_one_contact):
        self.wood_app = wood_app_submitted
        self.admin_client.post(CaseURLS.take_ownership(self.wood_app.pk))

        self.wood_app.refresh_from_db()
        self.wood_app.status = ImpExpStatus.VARIATION_REQUESTED
        self.wood_app.save()

        add_variation_request_to_app(
            self.wood_app, importer_one_contact, VariationRequest.Statuses.OPEN
        )
        self.vr = self.wood_app.variation_requests.get(status=VariationRequest.Statuses.OPEN)

        self.admin_client.post(
            CaseURLS.variation_request_request_update(self.wood_app.pk, self.vr.pk),
            {"update_request_reason": "Dummy update request reason"},
        )
        check_gov_notify_email_was_sent(
            1,
            ["I1_main_contact@example.com"],  # /PS-IGNORE
            EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED,
            {
                "reference": self.wood_app.reference,
                "validate_digital_signatures_url": get_validate_digital_signatures_url(
                    get_importer_site_domain()
                ),
                "application_url": get_case_view_url(self.wood_app, get_importer_site_domain()),
                "reason": "Dummy update request reason",
                "icms_url": get_importer_site_domain(),
                "service_name": SiteName.IMPORTER.label,
            },
        )
        mail.outbox = []

    def test_respond_to_update_request_get(self):
        response = self.client.get(
            CaseURLS.variation_request_submit_update(self.wood_app.pk, self.vr.pk)
        )

        assert response.status_code == 200
        context = response.context

        assert context["vr_num"] == 1
        assert context["object"].pk == self.vr.pk

    def test_respond_to_update_request_post(self):
        response = self.client.post(
            CaseURLS.variation_request_submit_update(self.wood_app.pk, self.vr.pk),
            {
                "what_varied": "What was varied now its changed",
                "why_varied": self.vr.why_varied,
                "when_varied": self.vr.when_varied.strftime(JQUERY_DATE_FORMAT),
            },
        )

        assertRedirects(response, reverse("workbasket"), 302)

        # Check the status is the same but VR_REQUEST_CHANGE is no longer an active task.
        self.wood_app.refresh_from_db()
        case_progress.check_expected_status(self.wood_app, [ImpExpStatus.VARIATION_REQUESTED])

        assert Task.TaskType.VR_REQUEST_CHANGE not in case_progress.get_active_task_list(
            self.wood_app
        )

        # Check the reason has been cleared and the what varied is updated.
        self.vr.refresh_from_db()
        assert self.vr.update_request_reason is None
        assert self.vr.what_varied == "What was varied now its changed"
        check_gov_notify_email_was_sent(
            1,
            ["ilb_admin_user@example.com"],  # /PS-IGNORE,
            EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_RECEIVED,
            {
                "reference": self.wood_app.reference,
                "validate_digital_signatures_url": get_validate_digital_signatures_url(
                    get_caseworker_site_domain()
                ),
                "application_url": get_case_view_url(self.wood_app, get_caseworker_site_domain()),
                "icms_url": get_caseworker_site_domain(),
                "service_name": SiteName.CASEWORKER.label,
            },
        )
