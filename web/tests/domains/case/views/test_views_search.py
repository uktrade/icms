from typing import TYPE_CHECKING

import pytest
from django.utils import timezone
from pytest_django.asserts import assertRedirects

from web.domains.case._import.wood.models import WoodQuotaApplication
from web.flow import errors
from web.flow.models import Task
from web.tests.helpers import SearchURLS

if TYPE_CHECKING:
    from django.test.client import Client


# TODO: ICMSLST-1240 Add permission tests for all views
# TODO Add tests
class TestSearchApplicationsView:
    ...


# TODO Add tests
class TestReassignCaseOwnerView:
    ...


# TODO Add tests
class TestDownloadSpreadsheetView:
    ...


class TestReopenApplicationView:
    client: "Client"
    wood_app: WoodQuotaApplication

    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, wood_app_submitted, test_icms_admin_user):
        self.wood_app = wood_app_submitted

        # End the PROCESS task as we are testing reopening the application
        task = self.wood_app.get_expected_task(Task.TaskType.PROCESS)
        task.is_active = False
        task.finished = timezone.now()
        task.owner = test_icms_admin_user
        task.save()

    def test_reopen_application_when_stopped(self, wood_app_submitted):
        self.wood_app.status = WoodQuotaApplication.Statuses.STOPPED
        self.wood_app.save()

        url = SearchURLS.reopen_case(application_pk=self.wood_app.pk)
        resp = self.client.post(url)

        self._check_valid_response(resp, wood_app_submitted)

    def test_reopen_application_when_withdrawn(self, wood_app_submitted):
        self.wood_app.status = WoodQuotaApplication.Statuses.WITHDRAWN
        self.wood_app.save()

        url = SearchURLS.reopen_case(application_pk=self.wood_app.pk)
        resp = self.client.post(url)

        self._check_valid_response(resp, wood_app_submitted)

    def test_reopen_application_when_processing_errors(self, wood_app_submitted):
        with pytest.raises(expected_exception=errors.ProcessStateError):
            url = SearchURLS.reopen_case(application_pk=self.wood_app.pk)
            self.client.post(url)

    def test_reopen_application_unsets_caseworker(self, test_icms_admin_user, wood_app_submitted):
        self.wood_app.status = WoodQuotaApplication.Statuses.STOPPED
        self.wood_app.case_owner = test_icms_admin_user
        self.wood_app.save()

        url = SearchURLS.reopen_case(application_pk=self.wood_app.pk)
        resp = self.client.post(url)

        self._check_valid_response(resp, wood_app_submitted)
        assert self.wood_app.case_owner is None

    def _check_valid_response(self, resp, application):
        assert resp.status_code == 204
        application.refresh_from_db()

        application.check_expected_status([application.Statuses.SUBMITTED])
        application.get_expected_task(Task.TaskType.PROCESS)


class TestRequestVariationUpdateView:
    client: "Client"
    wood_app: WoodQuotaApplication

    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, wood_app_submitted, test_icms_admin_user):
        self.wood_app = wood_app_submitted
        self.wood_app.status = WoodQuotaApplication.Statuses.COMPLETED
        self.wood_app.save()

        # End the PROCESS task as we are testing with a completed application
        task = self.wood_app.get_expected_task(Task.TaskType.PROCESS)
        task.is_active = False
        task.finished = timezone.now()
        task.owner = test_icms_admin_user
        task.save()

    def test_get_search_url(self):
        url = SearchURLS.request_variation(self.wood_app.pk)

        # Test referrer query params are remembered
        referrer = "http://localhost:8080/case/import/search/standard/results/?status=COMPLETED&decision=APPROVE"
        resp = self.client.get(url, HTTP_REFERER=referrer)

        expected = "/case/import/search/standard/results/?status=COMPLETED&decision=APPROVE"
        assert resp.context["search_results_url"] == expected

        # Test referrer set without query params
        referrer = "http://localhost:8080/case/import/search/standard/results/"
        resp = self.client.get(url, HTTP_REFERER=referrer)

        expected = "/case/import/search/standard/results/"
        assert resp.context["search_results_url"] == expected

    def test_get_search_url_no_referrer(self):
        url = SearchURLS.request_variation(self.wood_app.pk)
        resp = self.client.get(url)

        expected = "/case/import/search/standard/results/?case_status=VARIATION_REQUESTED"
        assert resp.context["search_results_url"] == expected

    def test_post_updates_status(self, test_icms_admin_user):
        url = SearchURLS.request_variation(self.wood_app.pk)

        form_data = {
            "what_varied": "What was varied",
            "why_varied": "Why was it varied",
            "when_varied": "01-Jan-2021",
        }

        # Set this fields as reopening a case should clear them.
        self.wood_app.case_owner = test_icms_admin_user
        self.wood_app.variation_decision = WoodQuotaApplication.REFUSE
        self.wood_app.variation_refuse_reason = "test value"

        resp = self.client.post(url, data=form_data)
        default_redirect_url = (
            "/case/import/search/standard/results/?case_status=VARIATION_REQUESTED"
        )

        assertRedirects(resp, default_redirect_url, 302)
        self.wood_app.refresh_from_db()

        assert not self.wood_app.case_owner
        assert not self.wood_app.variation_decision
        assert not self.wood_app.variation_refuse_reason

        self.wood_app.check_expected_status([WoodQuotaApplication.Statuses.VARIATION_REQUESTED])
        self.wood_app.get_expected_task(Task.TaskType.PROCESS)
