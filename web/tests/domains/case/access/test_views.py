from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertInHTML, assertRedirects, assertTemplateUsed

from web.mail.constants import EmailTypes
from web.models import AccessRequest, ExporterAccessRequest, ImporterAccessRequest
from web.permissions import organisation_get_contacts
from web.sites import (
    SiteName,
    get_caseworker_site_domain,
    get_exporter_site_domain,
    get_importer_site_domain,
)
from web.tests.auth import AuthTestCase
from web.tests.conftest import LOGIN_URL
from web.tests.helpers import check_gov_notify_email_was_sent, get_test_client


class TestAccessRequestListView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
    ):
        self.url = reverse("access:importer-list")

    def test_list_importer_access_request_ok(self, importer_access_request):
        response = self.importer_client.get(self.url)
        assert response.status_code == 403

        response = self.ilb_admin_client.get(self.url)

        assert response.status_code == 200
        assert "Search Importer Access Requests" in response.content.decode()
        assert response.context["object_list"].count() == 1

    def test_prefilled_importer_name(self):
        """Tests that the importer_name query parameter is used to prefill the search form."""
        prefilled_url = f"{self.url}?importer_name=Import Ltd"
        response = self.ilb_admin_client.get(prefilled_url)
        assert response.status_code == HTTPStatus.OK
        context = response.context
        assert context["filter"].form.fields["q"].initial == "Import Ltd"


class TestExporterAccessRequestListView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(
        self,
        _setup,
    ):
        self.url = reverse("access:exporter-list")

    def test_list_exporter_access_request_ok(self):
        response = self.exporter_client.get(self.url)

        assert response.status_code == 403

        response = self.ilb_admin_client.get(self.url)

        assert response.status_code == 200
        assert "Search Exporter Access Requests" in response.content.decode()
        assert response.context["object_list"].count() == 1

    def test_prefilled_exporter_name(self):
        """Tests that the exporter_name query parameter is used to prefill the search form."""
        prefilled_url = f"{self.url}?exporter_name=Export Ltd"
        response = self.ilb_admin_client.get(prefilled_url)
        assert response.status_code == HTTPStatus.OK
        context = response.context
        assert context["filter"].form.fields["q"].initial == "Export Ltd"


class TestImporterAccessRequestView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, access_request_user, importer_site):
        self.access_request_user = access_request_user
        self.access_request_client = get_test_client(importer_site.domain, access_request_user)
        self.url = reverse("access:importer-request")

    def test_permission(self):
        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.anonymous_client.get(self.url)
        assertRedirects(response, f"{LOGIN_URL}?next={self.url}")

    def test_get(self):
        response = self.access_request_client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        context = response.context
        # access_request_user is linked to an existing importer access request
        assert context["pending_importer_access_requests"].count() == 1

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
        check_gov_notify_email_was_sent(
            2,
            [
                "ilb_admin_user@example.com",  # /PS-IGNORE
                "ilb_admin_two@example.com",  # /PS-IGNORE
            ],
            EmailTypes.ACCESS_REQUEST,
            {
                "reference": "IAR/1",
                "icms_url": get_caseworker_site_domain(),
                "service_name": SiteName.CASEWORKER.label,
            },
        )


class TestExporterAccessRequestView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, access_request_user, exporter_site):
        self.access_request_user = access_request_user
        self.access_request_client = get_test_client(exporter_site.domain, access_request_user)
        self.url = reverse("access:exporter-request")

    def test_permission(self):
        response = self.exporter_client.get(self.url)
        assert response.status_code == HTTPStatus.OK

        response = self.importer_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.anonymous_client.get(self.url)
        assertRedirects(response, f"{LOGIN_URL}?next={self.url}")

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
        check_gov_notify_email_was_sent(
            2,
            [
                "ilb_admin_user@example.com",  # /PS-IGNORE
                "ilb_admin_two@example.com",  # /PS-IGNORE
            ],
            EmailTypes.ACCESS_REQUEST,
            {
                "reference": "EAR/1",
                "icms_url": get_caseworker_site_domain(),
                "service_name": SiteName.CASEWORKER.label,
            },
        )


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

        check_gov_notify_email_was_sent(
            1,
            [self.iar.submitted_by.email],
            EmailTypes.ACCESS_REQUEST_CLOSED,
            {
                "agent": "",
                "organisation": "Import Ltd",
                "outcome": "Approved",
                "reason": "",
                "request_type": "Importer",
                "icms_url": get_importer_site_domain(),
                "is_agent": "no",
                "has_been_refused": "no",
                "service_name": "apply for an import licence",
            },
        )

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

        check_gov_notify_email_was_sent(
            1,
            [self.iar.submitted_by.email],
            EmailTypes.ACCESS_REQUEST_CLOSED,
            {
                "agent": "",
                "organisation": "Import Ltd",
                "outcome": "Refused",
                "reason": "Reason: test refuse",
                "request_type": "Importer",
                "icms_url": get_importer_site_domain(),
                "is_agent": "no",
                "has_been_refused": "yes",
                "service_name": "apply for an import licence",
            },
        )

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

        check_gov_notify_email_was_sent(
            1,
            [self.ear.submitted_by.email],
            EmailTypes.ACCESS_REQUEST_CLOSED,
            {
                "agent": "",
                "organisation": "Export Ltd",
                "outcome": "Approved",
                "reason": "",
                "request_type": "Exporter",
                "icms_url": get_exporter_site_domain(),
                "is_agent": "no",
                "has_been_refused": "no",
                "service_name": "apply for an export certificate",
            },
        )

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

        check_gov_notify_email_was_sent(
            1,
            [self.ear.submitted_by.email],
            EmailTypes.ACCESS_REQUEST_CLOSED,
            {
                "agent": "",
                "organisation": "Export Ltd",
                "outcome": "Refused",
                "reason": "Reason: test refuse",
                "request_type": "Exporter",
                "icms_url": get_exporter_site_domain(),
                "is_agent": "no",
                "has_been_refused": "yes",
                "service_name": "apply for an export certificate",
            },
        )

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
