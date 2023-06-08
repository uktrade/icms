from http import HTTPStatus

import pytest
from django.core import mail
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects, assertTemplateUsed

from web.models import AccessRequest, ExporterAccessRequest, ImporterAccessRequest
from web.permissions import organisation_get_contacts
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
    @pytest.fixture(autouse=True)
    def setup(self, _setup, access_request_user, importer_access_request, exporter_access_request):
        self.acc_req_user = access_request_user

        self.iar = importer_access_request
        self.iar_url = reverse(
            "access:link-request",
            kwargs={"access_request_pk": importer_access_request.pk, "entity": "importer"},
        )

        self.ear = exporter_access_request
        self.ear_url = reverse(
            "access:link-request",
            kwargs={"access_request_pk": exporter_access_request.pk, "entity": "exporter"},
        )

    def test_permission(self):
        response = self.ilb_admin_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_link_importer_access_request(self):
        assert self.iar.link is None

        data = {"link": self.importer.pk}

        response = self.ilb_admin_client.post(self.iar_url, data=data)

        assertRedirects(response, self.iar_url)

        self.iar.refresh_from_db()

        assert self.iar.link == self.importer

    def test_link_importer_agent_access_request(self):
        assert self.iar.link is None
        assert self.iar.agent_link is None

        data = {"link": self.importer.pk, "agent_link": self.importer_agent.pk}

        response = self.ilb_admin_client.post(self.iar_url, data=data)

        assertRedirects(response, self.iar_url)

        self.iar.refresh_from_db()

        assert self.iar.link == self.importer
        assert self.iar.agent_link == self.importer_agent

    def test_link_exporter_access_request(self):
        assert self.ear.link is None

        data = {"link": self.exporter.pk}

        response = self.ilb_admin_client.post(self.ear_url, data=data)

        assertRedirects(response, self.ear_url)

        self.ear.refresh_from_db()

        assert self.ear.link == self.exporter

    def test_link_exporter_agent_access_request(self):
        assert self.ear.link is None
        assert self.ear.agent_link is None

        data = {"link": self.exporter.pk, "agent_link": self.exporter_agent.pk}

        response = self.ilb_admin_client.post(self.ear_url, data=data)

        assertRedirects(response, self.ear_url)

        self.ear.refresh_from_db()

        assert self.ear.link == self.exporter
        assert self.ear.agent_link == self.exporter_agent


class TestCloseAccessRequest(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, access_request_user, importer_access_request, exporter_access_request):
        self.acc_req_user = access_request_user

        self.iar = importer_access_request
        self.iar_url = reverse(
            "access:close-request",
            kwargs={"access_request_pk": importer_access_request.pk, "entity": "importer"},
        )

        self.ear = exporter_access_request
        self.ear_url = reverse(
            "access:close-request",
            kwargs={"access_request_pk": exporter_access_request.pk, "entity": "exporter"},
        )

    def test_permission(self, importer_access_request):
        response = self.ilb_admin_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_close_importer_access_request_approve(self):
        response = self.ilb_admin_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.OK

        # Test we can always close (even without linking)
        assertInHTML(
            '<button type="submit" class="button primary-button">Close Access Request</button>',
            response.content.decode(),
        )

        response = self.ilb_admin_client.post(
            self.iar_url, data={"response": AccessRequest.APPROVED}
        )
        assert response.status_code == 302

        self.iar.refresh_from_db()
        assert self.iar.response == AccessRequest.APPROVED

        self._assert_email_sent(self.iar)

    def test_close_importer_access_request_refuse(self):
        response = self.ilb_admin_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.OK

        response = self.ilb_admin_client.post(
            self.iar_url, data={"response": AccessRequest.REFUSED, "response_reason": "test refuse"}
        )
        assert response.status_code == 302

        self.iar.refresh_from_db()
        assert self.iar.response == AccessRequest.REFUSED
        assert self.iar.response_reason == "test refuse"

        self._assert_email_sent(self.iar)

    def test_close_exporter_access_request_approve(self):
        response = self.ilb_admin_client.get(self.ear_url)
        assert response.status_code == HTTPStatus.OK

        # Test we can always close (even without linking)
        assertInHTML(
            '<button type="submit" class="button primary-button">Close Access Request</button>',
            response.content.decode(),
        )

        response = self.ilb_admin_client.post(
            self.ear_url, data={"response": AccessRequest.APPROVED}
        )
        assert response.status_code == 302

        self.ear.refresh_from_db()
        assert self.ear.response == AccessRequest.APPROVED

        self._assert_email_sent(self.ear)

    def test_close_exporter_access_request_refuse(self):
        response = self.ilb_admin_client.get(self.ear_url)
        assert response.status_code == HTTPStatus.OK

        response = self.ilb_admin_client.post(
            self.ear_url, data={"response": AccessRequest.REFUSED, "response_reason": "test refuse"}
        )
        assert response.status_code == 302

        self.ear.refresh_from_db()
        assert self.ear.response == AccessRequest.REFUSED
        assert self.ear.response_reason == "test refuse"

        self._assert_email_sent(self.ear)

    def test_close_iar_approve_user_permissions(self):
        """Test approving a linked IAR adds the access request user as an org contact."""

        org_contacts = organisation_get_contacts(self.importer)
        assert not org_contacts.contains(self.acc_req_user)

        self.iar.link = self.importer
        self.iar.save()
        response = self.ilb_admin_client.post(
            self.iar_url, data={"response": AccessRequest.APPROVED}
        )
        assert response.status_code == 302

        org_contacts = organisation_get_contacts(self.importer)
        assert org_contacts.contains(self.acc_req_user)

    def test_close_iar_refuse_user_permissions(self):
        """Test refusing a linked IAR does not add the access request user as an org contact."""

        org_contacts = organisation_get_contacts(self.importer)
        assert not org_contacts.contains(self.acc_req_user)

        self.iar.link = self.importer
        self.iar.save()
        response = self.ilb_admin_client.post(
            self.iar_url, data={"response": AccessRequest.REFUSED, "response_reason": "test refuse"}
        )
        assert response.status_code == 302

        org_contacts = organisation_get_contacts(self.importer)
        assert not org_contacts.contains(self.acc_req_user)

    def test_close_iar_agent_approve_user_permissions(self):
        """Test approving a linked IAR adds the access request user as an org agent contact."""

        org_contacts = organisation_get_contacts(self.importer)
        assert not org_contacts.contains(self.acc_req_user)

        self.iar.link = self.importer
        self.iar.agent_link = self.importer_agent
        self.iar.request_type = ImporterAccessRequest.AGENT_ACCESS
        self.iar.save()

        response = self.ilb_admin_client.post(
            self.iar_url, data={"response": AccessRequest.APPROVED}
        )
        assert response.status_code == 302

        org_contacts = organisation_get_contacts(self.importer_agent)

        assert org_contacts.contains(self.acc_req_user)

    def test_close_iar_agent_refuse_user_permissions(self):
        """Test refusing a linked IAR does not add the access request user as an org agent contact."""

        org_contacts = organisation_get_contacts(self.importer)
        assert not org_contacts.contains(self.acc_req_user)

        self.iar.link = self.importer
        self.iar.agent_link = self.importer_agent
        self.iar.request_type = ImporterAccessRequest.AGENT_ACCESS
        self.iar.save()

        response = self.ilb_admin_client.post(
            self.iar_url, data={"response": AccessRequest.REFUSED, "response_reason": "test refuse"}
        )
        assert response.status_code == 302

        org_contacts = organisation_get_contacts(self.importer_agent)
        assert not org_contacts.contains(self.acc_req_user)

    def test_close_ear_approve_user_permissions(self):
        """Test approving a linked EAR adds the access request user as an org contact."""

        org_contacts = organisation_get_contacts(self.exporter)
        assert not org_contacts.contains(self.acc_req_user)

        self.ear.link = self.exporter
        self.ear.save()
        response = self.ilb_admin_client.post(
            self.ear_url, data={"response": AccessRequest.APPROVED}
        )
        assert response.status_code == 302

        org_contacts = organisation_get_contacts(self.exporter)
        assert org_contacts.contains(self.acc_req_user)

    def test_close_ear_refuse_user_permissions(self):
        """Test refusing a linked EAR does not add the access request user as an org contact."""

        org_contacts = organisation_get_contacts(self.exporter)
        assert not org_contacts.contains(self.acc_req_user)

        self.ear.link = self.exporter
        self.ear.save()
        response = self.ilb_admin_client.post(
            self.ear_url, data={"response": AccessRequest.REFUSED, "response_reason": "test refuse"}
        )
        assert response.status_code == 302

        org_contacts = organisation_get_contacts(self.exporter)
        assert not org_contacts.contains(self.acc_req_user)

    def test_close_ear_agent_approve_user_permissions(self):
        """Test approving a linked EAR adds the access request user as an org agent contact."""

        org_contacts = organisation_get_contacts(self.exporter)
        assert not org_contacts.contains(self.acc_req_user)

        self.ear.link = self.exporter
        self.ear.agent_link = self.exporter_agent
        self.ear.request_type = ExporterAccessRequest.AGENT_ACCESS
        self.ear.save()

        response = self.ilb_admin_client.post(
            self.ear_url, data={"response": AccessRequest.APPROVED}
        )
        assert response.status_code == 302

        org_contacts = organisation_get_contacts(self.exporter_agent)

        assert org_contacts.contains(self.acc_req_user)

    def test_close_ear_agent_refuse_user_permissions(self):
        """Test refusing a linked EAR does not add the access request user as an org agent contact."""

        org_contacts = organisation_get_contacts(self.exporter)
        assert not org_contacts.contains(self.acc_req_user)

        self.ear.link = self.exporter
        self.ear.agent_link = self.exporter_agent
        self.ear.request_type = ExporterAccessRequest.AGENT_ACCESS
        self.ear.save()

        response = self.ilb_admin_client.post(
            self.ear_url, data={"response": AccessRequest.REFUSED, "response_reason": "test refuse"}
        )
        assert response.status_code == 302

        org_contacts = organisation_get_contacts(self.exporter_agent)
        assert not org_contacts.contains(self.acc_req_user)

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


class TestAccessRequestHistoryView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, access_request_user, importer_access_request, exporter_access_request):
        self.acc_req_user = access_request_user

        self.iar = importer_access_request
        self.iar.link = self.importer
        self.iar.agent_link = self.importer_agent
        self.iar.request_type = ImporterAccessRequest.AGENT_ACCESS
        self.iar.status = ImporterAccessRequest.Statuses.CLOSED
        self.iar.response = ImporterAccessRequest.APPROVED
        self.iar.save()
        self.iar_url = reverse(
            "access:request-history", kwargs={"access_request_pk": importer_access_request.pk}
        )

        self.ear = exporter_access_request
        self.ear.link = self.exporter
        self.ear.agent_link = self.exporter_agent
        self.ear.request_type = ExporterAccessRequest.AGENT_ACCESS
        self.ear.status = ExporterAccessRequest.Statuses.CLOSED
        self.ear.response = ExporterAccessRequest.APPROVED
        self.ear.save()
        self.ear_url = reverse(
            "access:request-history", kwargs={"access_request_pk": exporter_access_request.pk}
        )

    def test_permission(self):
        response = self.ilb_admin_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.ilb_admin_client.get(self.ear_url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.ear_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.ear_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post_forbidden(self):
        response = self.ilb_admin_client.post(self.iar_url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

        response = self.ilb_admin_client.post(self.ear_url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    def test_get_importer_access_request_history(self):
        response = self.ilb_admin_client.get(self.iar_url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        resp_html = response.content.decode("utf-8")

        assert context["object"] == self.iar
        assert context["access_request"] == self.iar
        assert context["firs"].count() == 0
        assert context["approval_request"] is None
        assert context["entity"] == "importer"

        assertTemplateUsed(response, "web/domains/case/access/access-request-history.html")
        assertInHTML("Access Request", resp_html)
        assertInHTML("Request access to act as an Agent for an Importer", resp_html)
        assertInHTML("Further Information Requests", resp_html)
        assertInHTML("There aren't any further information requests.", resp_html)

    def test_get_exporter_access_request_history(self):
        response = self.ilb_admin_client.get(self.ear_url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        resp_html = response.content.decode("utf-8")

        assert context["object"] == self.ear
        assert context["access_request"] == self.ear
        assert context["firs"].count() == 0
        assert context["approval_request"] is None
        assert context["entity"] == "exporter"

        assertTemplateUsed(response, "web/domains/case/access/access-request-history.html")
        assertInHTML("Access Request", resp_html)
        assertInHTML("Request access to act as an Agent for an Exporter", resp_html)
        assertInHTML("Further Information Requests", resp_html)
        assertInHTML("There aren't any further information requests.", resp_html)
