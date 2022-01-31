import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertRedirects, assertTemplateUsed

from web.domains.case.models import VariationRequest
from web.domains.case.shared import ImpExpStatus
from web.flow.models import Task
from web.tests.helpers import CaseURLS


class TestVariationRequestManageView:
    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    def test_get_variations_for_import_application(self, test_icms_admin_user, wood_app_submitted):
        wood_app = wood_app_submitted
        self.client.post(CaseURLS.take_ownership(wood_app.pk))

        # Add a few previous variation requests
        _add_variation_request(wood_app, test_icms_admin_user, VariationRequest.REJECTED)
        _add_variation_request(wood_app, test_icms_admin_user, VariationRequest.ACCEPTED)
        # Add an open one last (as it's the latest)
        _add_variation_request(wood_app, test_icms_admin_user, VariationRequest.OPEN)

        response = self.client.get(CaseURLS.manage_variations(wood_app.pk))

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/case/manage/variations/import/manage.html")

        cd = response.context_data
        vrs = cd["variation_requests"]

        expected_status_order = [
            VariationRequest.OPEN,
            VariationRequest.ACCEPTED,
            VariationRequest.REJECTED,
        ]

        assert expected_status_order == [vr.status for vr in vrs]

    def test_get_variations_for_export_application(self, test_icms_admin_user, com_app_submitted):
        com_app = com_app_submitted

        self.client.post(CaseURLS.take_ownership(com_app.pk))

        # Add a few previous variation requests
        _add_variation_request(com_app, test_icms_admin_user, VariationRequest.CANCELLED)
        _add_variation_request(com_app, test_icms_admin_user, VariationRequest.CLOSED)
        # Add an open one last (as it's the latest)
        _add_variation_request(com_app, test_icms_admin_user, VariationRequest.OPEN)

        response = self.client.get(CaseURLS.manage_variations(com_app.pk, case_type="export"))

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/case/manage/variations/export/manage.html")

        cd = response.context_data
        vrs = cd["variation_requests"]

        expected_status_order = [
            VariationRequest.OPEN,
            VariationRequest.CLOSED,
            VariationRequest.CANCELLED,
        ]

        assert expected_status_order == [vr.status for vr in vrs]


class TestVariationRequestCancelView:
    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, wood_app_submitted, test_icms_admin_user):
        self.wood_app = wood_app_submitted
        self.client.post(CaseURLS.take_ownership(self.wood_app.pk))

        self.wood_app.refresh_from_db()
        self.wood_app.status = ImpExpStatus.VARIATION_REQUESTED
        _add_variation_request(self.wood_app, test_icms_admin_user)
        self.wood_app.save()

    def test_cancel_variation_request_get(self):
        vr = self.wood_app.variation_requests.first()
        resp = self.client.get(CaseURLS.cancel_variation_request(self.wood_app.pk, vr.pk))

        cd = resp.context_data

        assert resp.status_code == 200
        assert cd["object"] == vr
        assert cd["process"] == self.wood_app
        assert cd["page_title"] == f"Variations {self.wood_app.get_reference()}"
        assert cd["case_type"] == "import"

    def test_cancel_variation_request_post(self, test_icms_admin_user):
        vr = self.wood_app.variation_requests.first()
        resp = self.client.post(
            CaseURLS.cancel_variation_request(self.wood_app.pk, vr.pk),
            {"reject_cancellation_reason": "Test cancellation reason"},
        )

        assertRedirects(resp, reverse("workbasket"), 302)

        self.wood_app.refresh_from_db()
        vr.refresh_from_db()

        assert vr.status == VariationRequest.CANCELLED
        assert vr.reject_cancellation_reason == "Test cancellation reason"
        assert vr.closed_by == test_icms_admin_user
        assert vr.closed_datetime.date() == timezone.now().date()

        self.wood_app.check_expected_status([ImpExpStatus.COMPLETED])
        assert self.wood_app.get_active_task_list() == []


class TestVariationRequestCancelViewForExportApplication:
    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, com_app_submitted, test_icms_admin_user):
        self.app = com_app_submitted
        self.client.post(CaseURLS.take_ownership(self.app.pk))

        self.app.refresh_from_db()
        self.app.status = ImpExpStatus.VARIATION_REQUESTED
        _add_variation_request(self.app, test_icms_admin_user, VariationRequest.OPEN)
        self.app.save()

    def test_cancel_variation_request_post(self, test_icms_admin_user):
        vr = self.app.variation_requests.first()
        resp = self.client.post(
            CaseURLS.cancel_variation_request(self.app.pk, vr.pk, case_type="export")
        )

        assertRedirects(resp, reverse("workbasket"), 302)

        self.app.refresh_from_db()
        vr.refresh_from_db()

        assert vr.status == VariationRequest.CANCELLED
        assert vr.closed_by == test_icms_admin_user
        assert vr.closed_datetime.date() == timezone.now().date()

        self.app.check_expected_status([ImpExpStatus.COMPLETED])
        assert self.app.get_active_task_list() == []


class TestVariationRequestRequestUpdateView:
    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, wood_app_submitted, test_import_user):
        self.wood_app = wood_app_submitted
        self.client.post(CaseURLS.take_ownership(self.wood_app.pk))

        self.wood_app.refresh_from_db()
        self.wood_app.status = ImpExpStatus.VARIATION_REQUESTED
        self.wood_app.save()

        _add_variation_request(self.wood_app, test_import_user, VariationRequest.OPEN)
        self.vr = self.wood_app.variation_requests.get(status=VariationRequest.OPEN)

    def test_request_update_post(self):
        response = self.client.post(
            CaseURLS.variation_request_request_update(self.wood_app.pk, self.vr.pk),
            {"update_request_reason": "Dummy update request reason"},
        )

        redirect_url = CaseURLS.manage_variations(self.wood_app.pk)
        assertRedirects(response, redirect_url, 302)

        # Check the status is the same but the app has a new task
        self.wood_app.refresh_from_db()
        self.wood_app.check_expected_status([ImpExpStatus.VARIATION_REQUESTED])
        self.wood_app.get_expected_task(Task.TaskType.VR_REQUEST_CHANGE, select_for_update=False)

        # Check the reason has been saved
        self.vr.refresh_from_db()
        assert self.vr.update_request_reason == "Dummy update request reason"


class TestVariationRequestCancelUpdateRequestView:
    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, wood_app_submitted, test_import_user):
        self.app = wood_app_submitted
        self.client.post(CaseURLS.take_ownership(self.app.pk))

        self.app.refresh_from_db()
        self.app.status = ImpExpStatus.VARIATION_REQUESTED
        self.app.save()

        _add_variation_request(self.app, test_import_user, VariationRequest.OPEN)
        self.vr = self.app.variation_requests.get(status=VariationRequest.OPEN)

        self.client.post(
            CaseURLS.variation_request_request_update(self.app.pk, self.vr.pk),
            {"update_request_reason": "Dummy update request reason"},
        )

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

        self.app.check_expected_status([ImpExpStatus.VARIATION_REQUESTED])
        assert Task.TaskType.VR_REQUEST_CHANGE not in self.app.get_active_task_list()

        assert self.vr.update_request_reason is None


class TestVariationRequestRespondToUpdateRequestView:
    @pytest.fixture(autouse=True)
    def set_client(self, importer_client, icms_admin_client):
        self.client = importer_client
        self.admin_client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, set_client, wood_app_submitted, test_import_user):
        self.wood_app = wood_app_submitted
        self.admin_client.post(CaseURLS.take_ownership(self.wood_app.pk))

        self.wood_app.refresh_from_db()
        self.wood_app.status = ImpExpStatus.VARIATION_REQUESTED
        self.wood_app.save()

        _add_variation_request(self.wood_app, test_import_user, VariationRequest.OPEN)
        self.vr = self.wood_app.variation_requests.get(status=VariationRequest.OPEN)

        self.admin_client.post(
            CaseURLS.variation_request_request_update(self.wood_app.pk, self.vr.pk),
            {"update_request_reason": "Dummy update request reason"},
        )

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
                "when_varied": self.vr.when_varied.strftime(settings.DATE_INPUT_FORMATS[0]),
            },
        )

        assertRedirects(response, reverse("workbasket"), 302)

        # Check the status is the same but VR_REQUEST_CHANGE is no longer an active task.
        self.wood_app.refresh_from_db()
        self.wood_app.check_expected_status([ImpExpStatus.VARIATION_REQUESTED])

        assert Task.TaskType.VR_REQUEST_CHANGE not in self.wood_app.get_active_task_list()

        # Check the reason has been cleared and the what varied is updated.
        self.vr.refresh_from_db()
        assert self.vr.update_request_reason is None
        assert self.vr.what_varied == "What was varied now its changed"


def _add_variation_request(wood_application, user, status=VariationRequest.OPEN):
    wood_application.variation_requests.create(
        status=status,
        what_varied="Dummy what_varied",
        why_varied="Dummy why_varied",
        when_varied=timezone.now().date(),
        requested_by=user,
    )
