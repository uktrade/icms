from http import HTTPStatus
from unittest.mock import create_autospec

import mohawk
import pytest
from django.core import exceptions
from django.urls import reverse
from django.utils import timezone
from mohawk.util import parse_authorization_header
from pytest_django.asserts import assertTemplateUsed

from web.domains.case.shared import ImpExpStatus
from web.domains.chief import types
from web.domains.chief import views as chief_views
from web.domains.chief.client import HTTPMethod, make_hawk_sender
from web.models import ImportApplicationLicence, Task
from web.tests.helpers import CaseURLS
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
            accepted=[types.AcceptedLicence(id=str(self.chief_req.lite_hmrc_id))],
            rejected=[],
        )

        content = payload.json().encode("UTF-8")
        sender = make_testing_hawk_sender("POST", self.url, content=content, content_type=JSON_TYPE)

        response = self.client.post(
            self.url,
            payload.dict(),
            content_type=JSON_TYPE,
            HTTP_HAWK_AUTHENTICATION=sender.request_header,
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers.get("Content-Type") == "application/json"

        # This will blow up if the signature does not match.
        sender.accept_response(
            response_header=response.headers["Server-authorization"],
            content=response.content,
            content_type=response.headers["Content-type"],
        )

    def test_auth_invalid(self):
        url = reverse("chief:license-data-callback")
        response = self.client.post(url, HTTP_HAWK_AUTHENTICATION="Hawk foo")

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.headers.get("Content-Type") == "application/json"


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

        # Value mocked: mohawk.Receiver().parsed_header
        mohawk_mock.Receiver.return_value.parsed_header = parse_authorization_header(
            'Hawk id="dh37fgj492je"'  # /PS-IGNORE
            ', ts="1367076201"'
            ', nonce="NPHgnG"'
            ', ext="foo bar"'
            ', mac="CeWHy4d9kbLGhDlkyw2Nh3PJ7SDOdZDa267KH4ZaNMY="'  # /PS-IGNORE
        )

        # Value mocked: mohawk.Receiver().respond()
        mohawk_mock.Receiver.return_value.respond.return_value = (
            'Hawk id="ph37fgj492je"'  # /PS-IGNORE
            ', ext="foo bar"'
            ', mac="DeWHy4d9kbLGhDlkyw2Nh3PJ7SDOdZDa267KH4ZaNMY="'  # /PS-IGNORE
        )

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
            accepted=[types.AcceptedLicence(id=str(self.chief_req.lite_hmrc_id))],
            rejected=[],
        )
        response = self.client.post(
            self.url, data=payload.dict(), content_type=JSON_TYPE, HTTP_HAWK_AUTHENTICATION="foo"
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers.get("Content-Type") == "application/json"

        check_licence_approve_correct(self.app, self.licence, self.chief_wait_task)
        check_complete_chief_request_correct(self.chief_req)

    def test_callback_rejects_licence(self):
        payload = types.ChiefLicenceReplyResponseData(
            run_number=1,
            accepted=[],
            rejected=[
                types.RejectedLicence(
                    id=str(self.chief_req.lite_hmrc_id),
                    errors=[
                        types.ResponseError(
                            error_code=1,
                            error_msg="Test error message",
                        )
                    ],
                )
            ],
        )

        response = self.client.post(
            self.url, data=payload.dict(), content_type=JSON_TYPE, HTTP_HAWK_AUTHENTICATION="foo"
        )

        assert response.status_code == HTTPStatus.OK
        assert response.headers.get("Content-Type") == "application/json"
        check_licence_reject_correct(self.app, self.licence, self.chief_wait_task)
        check_fail_chief_request_correct(self.chief_req)

    def test_error_codes(self):
        # Test invalid payload
        mock_sentry = create_autospec(capture_exception)
        self.monkeypatch.setattr(chief_views, "capture_exception", mock_sentry)
        payload = {"invalid": "data"}

        response = self.client.post(
            self.url, data=payload, content_type=JSON_TYPE, HTTP_HAWK_AUTHENTICATION="foo"
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.headers.get("Content-Type") == "application/json"
        mock_sentry.assert_called_once()

        # test valid payload with unknown record
        mock_sentry.reset_mock()
        payload = types.ChiefLicenceReplyResponseData(
            run_number=1,
            accepted=[types.AcceptedLicence(id="unknown-key")],
            rejected=[],
        )

        response = self.client.post(
            self.url, data=payload.dict(), content_type=JSON_TYPE, HTTP_HAWK_AUTHENTICATION="foo"
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response.headers.get("Content-Type") == "application/json"
        mock_sentry.assert_called_once()

        # An authentication error
        mock_sentry.reset_mock()
        mock_validate_request = create_autospec(
            chief_views.validate_request, side_effect=exceptions.BadRequest
        )
        self.monkeypatch.setattr(chief_views, "validate_request", mock_validate_request)
        response = self.client.post(
            self.url, data={}, content_type=JSON_TYPE, HTTP_HAWK_AUTHENTICATION="foo"
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.headers.get("Content-Type") == "application/json"


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


class TestChiefRequestDataView:
    def test_can_see_request_data(self, db, fa_sil_app_with_chief, icms_admin_client):
        chief_req = fa_sil_app_with_chief.chief_references.latest("pk")

        url = reverse("chief:request-data", kwargs={"litehmrcchiefrequest_id": chief_req.pk})

        response = icms_admin_client.get(url)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert response.content == b'{"foo": "bar"}'


class TestCheckChiefProgressView:
    @pytest.fixture(autouse=True)
    def set_client(self, icms_admin_client):
        self.client = icms_admin_client

    @pytest.fixture(autouse=True)
    def set_app(self, fa_dfl_app_submitted):
        """Using the submitted app override the app to the state we want."""
        fa_dfl_app_submitted.status = ImpExpStatus.PROCESSING
        fa_dfl_app_submitted.save()

        self.app = fa_dfl_app_submitted
        self._create_new_task(Task.TaskType.CHIEF_WAIT)

    def test_ilb_admin_permission_required(self, importer_client, exporter_client):
        url = CaseURLS.check_chief_progress(self.app.pk)

        # self.client is an ilb_admin client
        response = self.client.get(url)
        assert response.status_code == HTTPStatus.OK

        response = importer_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = exporter_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_check_chief_progress_chief_wait(self):
        resp = self.client.get(CaseURLS.check_chief_progress(self.app.pk))
        assert resp.status_code == HTTPStatus.OK

        resp_data = resp.json()
        expected_msg = "Awaiting Response - Licence sent to CHIEF, we are awaiting a response"
        assert resp_data["msg"] == expected_msg
        assert resp_data["reload_workbasket"] is False

    def test_check_chief_progress_chief_error(self):
        self._create_new_task(Task.TaskType.CHIEF_ERROR)

        resp = self.client.get(CaseURLS.check_chief_progress(self.app.pk))
        assert resp.status_code == HTTPStatus.OK

        resp_data = resp.json()
        assert resp_data["msg"] == "Rejected - A rejected response has been received from CHIEF."
        assert resp_data["reload_workbasket"] is True

    def test_check_chief_progress_app_complete(self):
        self.app.status = ImpExpStatus.COMPLETED
        self.app.save()

        task = self.app.tasks.get(is_active=True)
        task.is_active = False
        task.finished = timezone.now()
        task.save()

        resp = self.client.get(CaseURLS.check_chief_progress(self.app.pk))
        assert resp.status_code == HTTPStatus.OK

        resp_data = resp.json()
        assert resp_data["msg"] == "Accepted - An accepted response has been received from CHIEF."
        assert resp_data["reload_workbasket"] is True

    def _create_new_task(self, new_task):
        task = self.app.tasks.get(is_active=True)
        task.is_active = False
        task.finished = timezone.now()
        task.save()

        Task.objects.create(process=self.app, task_type=new_task, previous=task)
