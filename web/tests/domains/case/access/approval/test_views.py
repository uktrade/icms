from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.mail.constants import EmailTypes
from web.models import ApprovalRequest
from web.sites import (
    get_caseworker_site_domain,
    get_exporter_site_domain,
    get_importer_site_domain,
)
from web.tests.auth import AuthTestCase
from web.tests.helpers import (
    add_approval_request,
    check_gov_notify_email_was_sent,
    get_linked_access_request,
)


class TestManageAccessApprovalView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(
        self, _setup, importer_access_request, exporter_access_request, exporter_secondary_contact
    ):
        # Link the access requests to the orgs.
        self.iar = get_linked_access_request(importer_access_request, self.importer)
        self.ear = get_linked_access_request(exporter_access_request, self.exporter)

        self.importer_url = reverse(
            "access:case-management-access-approval",
            kwargs={"access_request_pk": self.iar.pk, "entity": "importer"},
        )
        self.exporter_url = reverse(
            "access:case-management-access-approval",
            kwargs={"access_request_pk": self.ear.pk, "entity": "exporter"},
        )
        self.exporter_secondary_contact = exporter_secondary_contact

    def test_permission(self):
        for url in [self.importer_url, self.exporter_url]:
            response = self.ilb_admin_client.get(url)
            assert response.status_code == HTTPStatus.OK

            response = self.importer_client.get(url)
            assert response.status_code == HTTPStatus.FORBIDDEN

            response = self.exporter_client.get(url)
            assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get(self):
        # Check only active importer one contacts with manage are available
        response = self.ilb_admin_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        requested_from = context["form"].fields["requested_from"].queryset

        assert requested_from.count() == 1
        assert requested_from.first() == self.importer_user

        # Check only active exporter one contacts with manage are available
        response = self.ilb_admin_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        requested_from = context["form"].fields["requested_from"].queryset

        assert requested_from.count() == 2
        assert requested_from.first() == self.exporter_user
        assert requested_from.last() == self.exporter_secondary_contact

    def test_post_importer(self):
        form_data = {
            "status": ApprovalRequest.Statuses.DRAFT,
            "requested_from": self.importer_user.pk,
        }
        response = self.ilb_admin_client.post(self.importer_url, data=form_data)

        assertRedirects(response, self.importer_url, HTTPStatus.FOUND)

        approval_request = self.iar.approval_requests.get(is_active=True)
        assert approval_request.status == ApprovalRequest.Statuses.OPEN
        assert approval_request.requested_from == self.importer_user
        assert approval_request.access_request == self.iar
        assert approval_request.requested_by == self.ilb_admin_user

        check_gov_notify_email_was_sent(
            1,
            [self.importer_user.email],
            EmailTypes.IMPORTER_ACCESS_REQUEST_APPROVAL_OPENED,
            {"user_type": "user", "icms_url": get_importer_site_domain()},
        )

    def test_post_exporter(self):
        form_data = {
            "status": ApprovalRequest.Statuses.DRAFT,
            "requested_from": self.exporter_user.pk,
        }
        response = self.ilb_admin_client.post(self.exporter_url, data=form_data)

        assertRedirects(response, self.exporter_url, HTTPStatus.FOUND)

        approval_request = self.ear.approval_requests.get(is_active=True)
        assert approval_request.status == ApprovalRequest.Statuses.OPEN
        assert approval_request.requested_from == self.exporter_user
        assert approval_request.access_request == self.ear
        assert approval_request.requested_by == self.ilb_admin_user
        check_gov_notify_email_was_sent(
            2,
            [self.exporter_user.email, self.exporter_secondary_contact.email],
            EmailTypes.EXPORTER_ACCESS_REQUEST_APPROVAL_OPENED,
            {"user_type": "user", "icms_url": get_exporter_site_domain()},
        )


class TestManageAccessApprovalWithdrawView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, importer_access_request, exporter_access_request):
        # Link the access requests to the orgs.
        self.iar = get_linked_access_request(importer_access_request, self.importer)
        self.iar_approval = add_approval_request(self.iar, self.ilb_admin_user, self.importer_user)

        self.ear = get_linked_access_request(exporter_access_request, self.exporter)
        self.ear_approval = add_approval_request(self.ear, self.ilb_admin_user, self.exporter_user)

        self.importer_url = reverse(
            "access:case-management-approval-request-withdraw",
            kwargs={
                "access_request_pk": self.iar.pk,
                "entity": "importer",
                "approval_request_pk": self.iar_approval.pk,
            },
        )
        self.exporter_url = reverse(
            "access:case-management-approval-request-withdraw",
            kwargs={
                "access_request_pk": self.ear.pk,
                "entity": "exporter",
                "approval_request_pk": self.ear_approval.pk,
            },
        )

    def test_permission(self):
        for url in [self.importer_url, self.exporter_url]:
            response = self.ilb_admin_client.get(url)
            assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

            response = self.ilb_admin_client.post(url)
            assert response.status_code == HTTPStatus.FOUND

            response = self.importer_client.get(url)
            assert response.status_code == HTTPStatus.FORBIDDEN

            response = self.exporter_client.get(url)
            assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post(self):
        #
        # Test importer access approval request
        #
        assert self.iar_approval.status == ApprovalRequest.Statuses.OPEN

        response = self.ilb_admin_client.post(self.importer_url)

        assertRedirects(
            response,
            reverse(
                "access:case-management-access-approval",
                kwargs={"access_request_pk": self.iar.pk, "entity": "importer"},
            ),
        )

        self.iar_approval.refresh_from_db()
        assert self.iar_approval.status == ApprovalRequest.Statuses.CANCELLED

        #
        # Test exporter access approval request
        #
        assert self.ear_approval.status == ApprovalRequest.Statuses.OPEN

        response = self.ilb_admin_client.post(self.exporter_url)

        assertRedirects(
            response,
            reverse(
                "access:case-management-access-approval",
                kwargs={"access_request_pk": self.ear.pk, "entity": "exporter"},
            ),
        )

        self.ear_approval.refresh_from_db()
        assert self.ear_approval.status == ApprovalRequest.Statuses.CANCELLED


class TestTakeOwnershipAccessApprovalView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, importer_access_request, exporter_access_request):
        # Link the access requests to the orgs.
        self.iar = get_linked_access_request(importer_access_request, self.importer)
        self.iar_approval = add_approval_request(self.iar, self.ilb_admin_user)

        self.ear = get_linked_access_request(exporter_access_request, self.exporter)
        self.ear_approval = add_approval_request(self.ear, self.ilb_admin_user)

        self.importer_url = reverse(
            "access:case-approval-take-ownership",
            kwargs={"approval_request_pk": self.iar_approval.pk, "entity": "importer"},
        )
        self.exporter_url = reverse(
            "access:case-approval-take-ownership",
            kwargs={"approval_request_pk": self.ear_approval.pk, "entity": "exporter"},
        )

    def test_permission(self):
        #
        # Test importer url
        #
        response = self.ilb_admin_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

        response = self.ilb_admin_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FOUND

        # Need to reset requested_from
        self.iar_approval.requested_from = None
        self.iar_approval.save()
        response = self.importer_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.exporter_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        #
        # Test exporter url
        #
        response = self.ilb_admin_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

        response = self.ilb_admin_client.post(self.exporter_url)
        assert response.status_code == HTTPStatus.FOUND

        # Need to reset requested_from
        self.ear_approval.requested_from = None
        self.ear_approval.save()
        response = self.exporter_client.post(self.exporter_url)
        assert response.status_code == HTTPStatus.FOUND

        response = self.importer_client.post(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_post(self):
        response = self.importer_client.post(self.importer_url)

        assert response.status_code == HTTPStatus.FOUND
        self.iar_approval.refresh_from_db()
        assert self.iar_approval.requested_from == self.importer_user

        response = self.exporter_client.post(self.exporter_url)

        assert response.status_code == HTTPStatus.FOUND
        self.ear_approval.refresh_from_db()
        assert self.ear_approval.requested_from == self.exporter_user


class TestReleaseOwnershipAccessApprovalView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, importer_access_request, exporter_access_request):
        # Link the access requests to the orgs.
        self.iar = get_linked_access_request(importer_access_request, self.importer)
        self.iar_approval = add_approval_request(self.iar, self.ilb_admin_user, self.importer_user)

        self.ear = get_linked_access_request(exporter_access_request, self.exporter)
        self.ear_approval = add_approval_request(self.ear, self.ilb_admin_user, self.exporter_user)

        self.importer_url = reverse(
            "access:case-approval-release-ownership",
            kwargs={"approval_request_pk": self.iar_approval.pk, "entity": "importer"},
        )
        self.exporter_url = reverse(
            "access:case-approval-release-ownership",
            kwargs={"approval_request_pk": self.ear_approval.pk, "entity": "exporter"},
        )

    def test_permission(self):
        #
        # Test importer url
        #
        response = self.ilb_admin_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

        response = self.ilb_admin_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.importer_client.post(self.importer_url)
        assert response.status_code == HTTPStatus.FOUND

        #
        # Test exporter url
        #
        response = self.ilb_admin_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

        response = self.ilb_admin_client.post(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.importer_client.post(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.post(self.exporter_url)
        assert response.status_code == HTTPStatus.FOUND

    def test_post(self):
        assert self.iar_approval.requested_from == self.importer_user
        response = self.importer_client.post(self.importer_url)

        assert response.status_code == HTTPStatus.FOUND
        self.iar_approval.refresh_from_db()
        assert self.iar_approval.requested_from is None

        assert self.ear_approval.requested_from == self.exporter_user
        response = self.exporter_client.post(self.exporter_url)

        assert response.status_code == HTTPStatus.FOUND
        self.ear_approval.refresh_from_db()
        assert self.ear_approval.requested_from is None


class TestCloseAccessApprovalView(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, importer_access_request, exporter_access_request):
        # Link the access requests to the orgs.
        self.iar = get_linked_access_request(importer_access_request, self.importer)
        self.iar_approval = add_approval_request(self.iar, self.ilb_admin_user, self.importer_user)

        self.ear = get_linked_access_request(exporter_access_request, self.exporter)
        self.ear_approval = add_approval_request(self.ear, self.ilb_admin_user, self.exporter_user)

        self.importer_url = reverse(
            "access:case-approval-respond",
            kwargs={
                "access_request_pk": self.iar.pk,
                "entity": "importer",
                "approval_request_pk": self.iar_approval.pk,
            },
        )
        self.exporter_url = reverse(
            "access:case-approval-respond",
            kwargs={
                "access_request_pk": self.ear.pk,
                "entity": "exporter",
                "approval_request_pk": self.ear_approval.pk,
            },
        )

    def test_permission(self):
        #
        # Test importer url
        #
        response = self.ilb_admin_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.importer_client.get(self.importer_url)
        assert response.status_code == HTTPStatus.OK

        #
        # Test exporter url
        #
        response = self.ilb_admin_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.importer_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.FORBIDDEN

        response = self.exporter_client.get(self.exporter_url)
        assert response.status_code == HTTPStatus.OK

    def test_post_approve_importer(self):
        form_data = {"response": ApprovalRequest.Responses.APPROVE, "response_reason": ""}

        response = self.importer_client.post(self.importer_url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        self.iar_approval.refresh_from_db()
        assert self.iar_approval.response == ApprovalRequest.Responses.APPROVE
        assert self.iar_approval.response_reason == ""
        assert self.iar_approval.status == ApprovalRequest.Statuses.COMPLETED
        assert self.iar_approval.response_by == self.importer_user

        check_gov_notify_email_was_sent(
            2,
            ["ilb_admin_user@example.com", "ilb_admin_two@example.com"],  # /PS-IGNORE
            EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE,
            {"user_type": "user", "icms_url": get_caseworker_site_domain()},
        )

    def test_post_approve_exporter(self):
        form_data = {"response": ApprovalRequest.Responses.APPROVE, "response_reason": ""}

        response = self.exporter_client.post(self.exporter_url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        self.ear_approval.refresh_from_db()
        assert self.ear_approval.response == ApprovalRequest.Responses.APPROVE
        assert self.ear_approval.response_reason == ""
        assert self.ear_approval.status == ApprovalRequest.Statuses.COMPLETED
        assert self.ear_approval.response_by == self.exporter_user
        check_gov_notify_email_was_sent(
            2,
            ["ilb_admin_user@example.com", "ilb_admin_two@example.com"],  # /PS-IGNORE
            EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE,
            {"user_type": "user", "icms_url": get_caseworker_site_domain()},
        )

    def test_post_refuse_importer(self):
        form_data = {
            "response": ApprovalRequest.Responses.REFUSE,
            "response_reason": "test response reason",
        }
        response = self.importer_client.post(self.importer_url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        self.iar_approval.refresh_from_db()
        assert self.iar_approval.response == ApprovalRequest.Responses.REFUSE
        assert self.iar_approval.response_reason == "test response reason"
        assert self.iar_approval.status == ApprovalRequest.Statuses.COMPLETED
        assert self.iar_approval.response_by == self.importer_user
        check_gov_notify_email_was_sent(
            2,
            ["ilb_admin_user@example.com", "ilb_admin_two@example.com"],  # /PS-IGNORE
            EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE,
            {"user_type": "user", "icms_url": get_caseworker_site_domain()},
        )

    def test_post_refuse_exporter(self):
        form_data = {
            "response": ApprovalRequest.Responses.REFUSE,
            "response_reason": "test response reason",
        }
        response = self.exporter_client.post(self.exporter_url, data=form_data)
        assert response.status_code == HTTPStatus.FOUND

        self.ear_approval.refresh_from_db()
        assert self.ear_approval.response == ApprovalRequest.Responses.REFUSE
        assert self.ear_approval.response_reason == "test response reason"
        assert self.ear_approval.status == ApprovalRequest.Statuses.COMPLETED
        assert self.ear_approval.response_by == self.exporter_user
        check_gov_notify_email_was_sent(
            2,
            ["ilb_admin_user@example.com", "ilb_admin_two@example.com"],  # /PS-IGNORE
            EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE,
            {"user_type": "user", "icms_url": get_caseworker_site_domain()},
        )
