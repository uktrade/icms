from http import HTTPStatus

from django.core import mail
from django.urls import reverse
from pytest_django.asserts import assertInHTML

from web.tests.auth import AuthTestCase
from web.tests.domains.case.access.factories import (
    ExporterAccessRequestFactory,
    ImporterAccessRequestFactory,
)


def test_list_importer_access_request_ok(importer_client, ilb_admin_client):
    response = importer_client.get("/access/importer/")
    assert response.status_code == 403

    ImporterAccessRequestFactory.create()
    response = ilb_admin_client.get("/access/importer/")

    assert response.status_code == 200
    assert "Search Importer Access Requests" in response.content.decode()


def test_list_exporter_access_request_ok(exporter_client, ilb_admin_client):
    response = exporter_client.get("/access/exporter/")

    assert response.status_code == 403

    ExporterAccessRequestFactory.create()
    response = ilb_admin_client.get("/access/exporter/")

    assert response.status_code == 200
    assert "Search Exporter Access Requests" in response.content.decode()


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
