from http import HTTPStatus

import pytest
from django.core import mail
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects

from web.tests.auth import AuthTestCase
from web.tests.helpers import get_test_client


def test_list_importer_access_request_ok(
    importer_client, ilb_admin_client, importer_access_request
):
    url = reverse("access:importer-list")

    response = importer_client.get(url)
    assert response.status_code == 403

    response = ilb_admin_client.get(url)

    assert response.status_code == 200
    assert "Search Importer Access Requests" in response.content.decode()
    assert response.context["object_list"].count() == 1


def test_list_exporter_access_request_ok(
    exporter_client, ilb_admin_client, exporter_access_request
):
    url = reverse("access:exporter-list")

    response = exporter_client.get(url)

    assert response.status_code == 403

    response = ilb_admin_client.get(url)

    assert response.status_code == 200
    assert "Search Exporter Access Requests" in response.content.decode()
    assert response.context["object_list"].count() == 1


class TestImporterAccessRequestView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, access_request_user):
        self.access_request_user = access_request_user
        self.access_request_client = get_test_client(access_request_user)
        self.login_url = reverse("login")
        self.url = reverse("access:importer-request")

    def test_permission(self):
        ok_clients = [
            self.access_request_client,
            self.exporter_client,
            self.importer_client,
            self.ilb_admin_client,
        ]
        redirect_clients = [self.anonymous_client]

        for client in ok_clients:
            response = client.get(self.url)

            assert response.status_code == HTTPStatus.OK

        for client in redirect_clients:
            response = client.get(self.url)

            assertRedirects(response, f"{self.login_url}?next={self.url}")

    def test_get(self):
        response = self.access_request_client.get(self.url)

        assert response.status_code == HTTPStatus.OK
        context = response.context

        # access_request_user is linked to an existing importer access request
        assert context["pending_importer_access_requests"].count() == 1

        # access_request_user is linked to an existing exporter access request
        assert context["pending_exporter_access_requests"].count() == 1

    def test_post(self):
        # access_request_user is linked to an existing importer & exporter access request
        assert self.access_request_user.submitted_access_requests.count() == 2

        form_data = {
            "request_type": "MAIN_IMPORTER_ACCESS",
            "organisation_name": "A Test Org",
            "organisation_address": "A Test Org Address",
            "request_reason": "A test reason",
        }

        response = self.access_request_client.post(self.url, data=form_data)

        redirect_url = reverse("access:requested")
        assertRedirects(response, redirect_url)

        self.access_request_user.refresh_from_db()

        assert self.access_request_user.submitted_access_requests.count() == 3


class TestExporterAccessRequestView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, access_request_user):
        self.access_request_user = access_request_user
        self.access_request_client = get_test_client(access_request_user)
        self.login_url = reverse("login")
        self.url = reverse("access:exporter-request")

    def test_permission(self):
        ok_clients = [
            self.access_request_client,
            self.exporter_client,
            self.importer_client,
            self.ilb_admin_client,
        ]
        redirect_clients = [self.anonymous_client]

        for client in ok_clients:
            response = client.get(self.url)

            assert response.status_code == HTTPStatus.OK

        for client in redirect_clients:
            response = client.get(self.url)

            assertRedirects(response, f"{self.login_url}?next={self.url}")

    def test_get(self):
        response = self.access_request_client.get(self.url)

        assert response.status_code == HTTPStatus.OK
        context = response.context

        # access_request_user is linked to an existing importer access request
        assert context["pending_importer_access_requests"].count() == 1

        # access_request_user is linked to an existing exporter access request
        assert context["pending_exporter_access_requests"].count() == 1

    def test_post(self):
        # access_request_user is linked to an existing importer & exporter access request
        assert self.access_request_user.submitted_access_requests.count() == 2

        form_data = {
            "request_type": "MAIN_EXPORTER_ACCESS",
            "organisation_name": "A Test Org",
            "organisation_address": "A Test Org Address",
            "request_reason": "A test reason",
        }

        response = self.access_request_client.post(self.url, data=form_data)

        redirect_url = reverse("access:requested")
        assertRedirects(response, redirect_url)

        self.access_request_user.refresh_from_db()

        assert self.access_request_user.submitted_access_requests.count() == 3


class TestLinkAccessRequest(AuthTestCase):
    # TODO: ICMSLST-2018 Add tests for "access:link-request"
    ...


class TestCloseAccessRequest(AuthTestCase):
    def test_permission(self, importer_access_request):
        url = reverse(
            "access:close-request", kwargs={"pk": importer_access_request.pk, "entity": "importer"}
        )

        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_close_importer_access_request_approve(self, importer_access_request):
        url = reverse(
            "access:close-request", kwargs={"pk": importer_access_request.pk, "entity": "importer"}
        )
        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        # Test we can always close (even without linking)
        assertInHTML(
            '<button type="submit" class="button primary-button">Close Access Request</button>',
            response.content.decode(),
        )

        response = self.ilb_admin_client.post(url, data={"response": "APPROVED"})
        assert response.status_code == 302

        importer_access_request.refresh_from_db()
        assert importer_access_request.response == "APPROVED"

        self._assert_email_sent(importer_access_request)

    def test_close_importer_access_request_refuse(self, importer_access_request):
        url = reverse(
            "access:close-request", kwargs={"pk": importer_access_request.pk, "entity": "importer"}
        )
        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        response = self.ilb_admin_client.post(
            url, data={"response": "REFUSED", "response_reason": "test refuse"}
        )
        assert response.status_code == 302

        importer_access_request.refresh_from_db()
        assert importer_access_request.response == "REFUSED"
        assert importer_access_request.response_reason == "test refuse"

        self._assert_email_sent(importer_access_request)

    def test_close_exporter_access_request_approve(self, exporter_access_request):
        url = reverse(
            "access:close-request", kwargs={"pk": exporter_access_request.pk, "entity": "exporter"}
        )
        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        # Test we can always close (even without linking)
        assertInHTML(
            '<button type="submit" class="button primary-button">Close Access Request</button>',
            response.content.decode(),
        )

        response = self.ilb_admin_client.post(url, data={"response": "APPROVED"})
        assert response.status_code == 302

        exporter_access_request.refresh_from_db()
        assert exporter_access_request.response == "APPROVED"

        self._assert_email_sent(exporter_access_request)

    def test_close_exporter_access_request_refuse(self, exporter_access_request):
        url = reverse(
            "access:close-request", kwargs={"pk": exporter_access_request.pk, "entity": "exporter"}
        )
        response = self.ilb_admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        response = self.ilb_admin_client.post(
            url, data={"response": "REFUSED", "response_reason": "test refuse"}
        )
        assert response.status_code == 302

        exporter_access_request.refresh_from_db()
        assert exporter_access_request.response == "REFUSED"
        assert exporter_access_request.response_reason == "test refuse"

        self._assert_email_sent(exporter_access_request)

    def _assert_email_sent(self, access_request):
        requester = access_request.submitted_by
        # The underlying code actually uses personal emails with portal_notifications set to True
        expected_to_email = requester.email

        outbox = mail.outbox

        assert len(outbox) == 1
        first_email = outbox[0]
        assert first_email.to == [expected_to_email]
        assert first_email.subject == "Import Case Management System Account"

        assert f"Request Outcome: {access_request.response}" in first_email.body
        if access_request.response:
            assert access_request.response in first_email.body
