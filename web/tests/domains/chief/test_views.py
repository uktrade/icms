from http import HTTPStatus
from unittest.mock import create_autospec

import mohawk
import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from web.domains.chief import types
from web.domains.chief import views as chief_views
from web.domains.chief.client import HTTPMethod, make_hawk_sender
from web.models import ImportApplicationLicence, Task
from web.utils.sentry import capture_exception

from .conftest import (
    check_complete_chief_request_correct,
    check_fail_chief_request_correct,
    check_licence_approve_correct,
    check_licence_reject_correct,
)

JSON_TYPE = "application/json"
# This has to match the request, because it is used to calculate the request's
# Hawk MAC digest. Django's test client uses "testserver" by default.
SERVER_NAME = "testserver"


def make_testing_hawk_sender(method: HTTPMethod, url: str, **kwargs):
    url = f"http://{SERVER_NAME}{url}"

    return make_hawk_sender(method, url, **kwargs)


class TestLicenseDataCallbackAuthentication:
    @pytest.fixture(autouse=True)
    def _setup(self, client, test_import_user, fa_sil_app_with_chief):
        self.client = client
        self.user = test_import_user
        self.app = fa_sil_app_with_chief
        self.url = reverse("chief:license-data-callback")

        # Current draft licence
        self.licence = self.app.licences.get(status=ImportApplicationLicence.Status.DRAFT)

        # Current active task
        self.chief_wait_task = self.app.tasks.get(task_type=Task.TaskType.CHIEF_WAIT)

        # The current LiteHMRCChiefRequest record
        self.chief_req = self.app.chief_references.first()

    def test_auth_valid(self):
        """The following test is testing the following mechanism:

        There are two parties involved in Hawk communication: a sender and a receiver.
        They use a shared secret to sign and verify each other’s messages.

        Sender
            A client who wants to access a Hawk-protected resource.
            The client will sign their request and upon receiving a response will also verify the response signature.

        Receiver
            A server that uses Hawk to protect its resources.
            The server will check the signature of an incoming request before accepting it.
            It also signs its response using the same shared secret.
        """

        payload = types.ChiefLicenceReplyResponseData(
            run_number=1,
            accepted=[types.AcceptedLicence(lite_hmrc_id=str(self.chief_req.lite_hmrc_id))],
            rejected=[],
        )

        content = payload.json().encode("UTF-8")
        sender = make_testing_hawk_sender("POST", self.url, content=content, content_type=JSON_TYPE)

        response = self.client.post(
            self.url,
            payload.dict(),
            content_type=JSON_TYPE,
            HTTP_AUTHORIZATION=sender.request_header,
        )

        assert response.status_code == HTTPStatus.OK

        # This will blow up if the signature does not match.
        sender.accept_response(
            response_header=response.headers["Server-authorization"],
            content=response.content,
            content_type=response.headers["Content-type"],
        )

    def test_auth_invalid(self):
        url = reverse("chief:license-data-callback")
        response = self.client.post(url, HTTP_AUTHORIZATION="Hawk foo")

        assert response.status_code == HTTPStatus.BAD_REQUEST


class TestLicenseDataCallbackView:
    @pytest.fixture(autouse=True)
    def _setup(self, client, test_import_user, fa_sil_app_with_chief, monkeypatch):
        self.client = client
        self.user = test_import_user
        self.app = fa_sil_app_with_chief
        self.monkeypatch = monkeypatch
        self.url = reverse("chief:license-data-callback")

        # Fake mohawk when testing the business logic for simplicity and speed.
        # See TestLicenseDataCallbackAuthentication above for authentication testing
        mohawk_mock = create_autospec(mohawk)
        self.monkeypatch.setattr(chief_views, "mohawk", mohawk_mock)

        # Current draft licence
        self.licence = self.app.licences.get(status=ImportApplicationLicence.Status.DRAFT)

        # Current active task
        self.chief_wait_task = self.app.tasks.get(task_type=Task.TaskType.CHIEF_WAIT)

        # The current LiteHMRCChiefRequest record
        self.chief_req = self.app.chief_references.first()

    def test_callback_approves_licence(self):
        payload = types.ChiefLicenceReplyResponseData(
            run_number=1,
            accepted=[types.AcceptedLicence(lite_hmrc_id=str(self.chief_req.lite_hmrc_id))],
            rejected=[],
        )
        response = self.client.post(
            self.url, data=payload.dict(), content_type=JSON_TYPE, HTTP_AUTHORIZATION="foo"
        )

        assert response.status_code == HTTPStatus.OK

        check_licence_approve_correct(self.app, self.licence, self.chief_wait_task)
        check_complete_chief_request_correct(self.chief_req)

    def test_callback_rejects_licence(self):
        payload = types.ChiefLicenceReplyResponseData(
            run_number=1,
            accepted=[],
            rejected=[
                types.RejectedLicence(
                    lite_hmrc_id=str(self.chief_req.lite_hmrc_id),
                    error_code=1,
                    error_msg="Test error message",
                )
            ],
        )

        response = self.client.post(
            self.url, data=payload.dict(), content_type=JSON_TYPE, HTTP_AUTHORIZATION="foo"
        )

        assert response.status_code == HTTPStatus.OK
        check_licence_reject_correct(self.app, self.licence, self.chief_wait_task)
        check_fail_chief_request_correct(self.chief_req)

    def test_error_codes(self):
        # Test invalid payload
        mock_sentry = create_autospec(capture_exception)
        self.monkeypatch.setattr(chief_views, "capture_exception", mock_sentry)
        payload = {"invalid": "data"}

        response = self.client.post(
            self.url, data=payload, content_type=JSON_TYPE, HTTP_AUTHORIZATION="foo"
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        mock_sentry.assert_called_once()

        # test valid payload with unknown record
        mock_sentry.reset_mock()
        payload = types.ChiefLicenceReplyResponseData(
            run_number=1,
            accepted=[types.AcceptedLicence(lite_hmrc_id="unknown-key")],
            rejected=[],
        )

        response = self.client.post(
            self.url, data=payload.dict(), content_type=JSON_TYPE, HTTP_AUTHORIZATION="foo"
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        mock_sentry.assert_called_once()


@pytest.mark.django_db
class TestPendingBatches:
    def test_template_context(self, icms_admin_client):
        url = reverse("chief:pending-batches")
        response = icms_admin_client.get(url)

        assert response.status_code == 200
        assert response.context_data["pending_batches_count"] == 0
        assert list(response.context_data["pending_batches"]) == []
        assertTemplateUsed(response, "web/domains/chief/pending_batches.html")


@pytest.mark.django_db
class TestFailedBatches:
    def test_template_context(self, icms_admin_client):
        url = reverse("chief:failed-batches")
        response = icms_admin_client.get(url)

        assert response.status_code == 200
        assert response.context_data["failed_batches_count"] == 0
        assert list(response.context_data["failed_batches"]) == []
        assertTemplateUsed(response, "web/domains/chief/failed_batches.html")


@pytest.mark.django_db
class TestPendingLicences:
    def test_template_context(self, icms_admin_client):
        url = reverse("chief:pending-licences")
        response = icms_admin_client.get(url)

        assert response.status_code == 200
        assert response.context_data["pending_licences_count"] == 0
        assert list(response.context_data["pending_licences"]) == []
        assertTemplateUsed(response, "web/domains/chief/pending_licences.html")


@pytest.mark.django_db
class TestFailedLicences:
    def test_template_context(self, icms_admin_client):
        url = reverse("chief:failed-licences")
        response = icms_admin_client.get(url)

        assert response.status_code == 200
        assert response.context_data["failed_licences_count"] == 0
        assert list(response.context_data["failed_licences"]) == []
        assertTemplateUsed(response, "web/domains/chief/failed_licences.html")
