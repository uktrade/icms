from unittest import mock
from urllib.parse import urljoin

import freezegun
import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from web.domains.case.services import document_pack
from web.mail import emails
from web.mail.constants import EmailTypes, VariationRequestDescription
from web.mail.url_helpers import get_case_view_url, get_validate_digital_signatures_url
from web.models import (
    EmailTemplate,
    ExporterAccessRequest,
    FirearmsAuthority,
    FurtherInformationRequest,
    ImporterAccessRequest,
    Section5Authority,
    UpdateRequest,
    VariationRequest,
    WithdrawApplication,
)
from web.sites import (
    get_caseworker_site_domain,
    get_exporter_site_domain,
    get_importer_site_domain,
)
from web.tests.auth.auth import AuthTestCase
from web.tests.helpers import (
    add_approval_request,
    add_variation_request_to_app,
    get_linked_access_request,
)


def default_personalisation() -> dict:
    return {
        "icms_contact_email": settings.ILB_CONTACT_EMAIL,
        "icms_contact_phone": settings.ILB_CONTACT_PHONE,
        "subject": "",
        "body": "",
    }


def get_gov_notify_template_id(email_type: EmailTypes):
    return str(EmailTemplate.objects.get(name=email_type).gov_notify_template_id)


class TestEmails(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, mock_gov_notify_client):
        self.mock_gov_notify_client = mock_gov_notify_client

    def test_access_request_email(self, importer_access_request):
        exp_template_id = get_gov_notify_template_id(EmailTypes.ACCESS_REQUEST)
        expected_personalisation = default_personalisation() | {
            "reference": importer_access_request.reference,
            "icms_url": get_caseworker_site_domain(),
        }
        emails.send_access_requested_email(importer_access_request)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 2
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_two_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_importer_access_request_closed_email(self, importer_access_request):
        importer_access_request.response = ImporterAccessRequest.APPROVED
        importer_access_request.request_type = ImporterAccessRequest.AGENT_ACCESS
        exp_template_id = get_gov_notify_template_id(EmailTypes.ACCESS_REQUEST_CLOSED)
        expected_personalisation = default_personalisation() | {
            "agent": "Agent ",
            "organisation": "Import Ltd",
            "outcome": "Approved",
            "reason": "",
            "request_type": "Importer",
            "icms_url": get_importer_site_domain(),
        }
        emails.send_access_request_closed_email(importer_access_request)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            importer_access_request.submitted_by.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_exporter_access_request_closed_email(self, exporter_access_request):
        exporter_access_request.response = ExporterAccessRequest.REFUSED
        exporter_access_request.request_type = ExporterAccessRequest.MAIN_EXPORTER_ACCESS
        exp_template_id = get_gov_notify_template_id(EmailTypes.ACCESS_REQUEST_CLOSED)
        expected_personalisation = default_personalisation() | {
            "agent": "",
            "organisation": "Export Ltd",
            "outcome": "Refused",
            "reason": "",
            "request_type": "Exporter",
            "icms_url": get_exporter_site_domain(),
        }
        emails.send_access_request_closed_email(exporter_access_request)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            exporter_access_request.submitted_by.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_access_request_closed_request_type_email(self, exporter_access_request):
        exporter_access_request.REQUEST_TYPE = "UNKNOWN"
        with pytest.raises(ValueError, match="Unknown access request type: UNKNOWN"):
            emails.send_access_request_closed_email(exporter_access_request)

    def test_exporter_send_approval_request_opened_email(self, exporter_access_request):
        ear = get_linked_access_request(exporter_access_request, self.exporter)
        ear_approval = add_approval_request(ear, self.ilb_admin_user, self.exporter_user)
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.EXPORTER_ACCESS_REQUEST_APPROVAL_OPENED
        )
        expected_personalisation = default_personalisation() | {
            "user_type": "user",
            "icms_url": get_exporter_site_domain(),
        }
        emails.send_approval_request_opened_email(ear_approval)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.exporter_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_importer_send_approval_request_opened_email(self, importer_access_request):
        iar = get_linked_access_request(importer_access_request, self.importer)
        iar.agent_link = self.importer_agent
        iar.request_type = ImporterAccessRequest.AGENT_ACCESS
        iar.save()

        iar_approval = add_approval_request(iar, self.ilb_admin_user, self.importer_user)
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.IMPORTER_ACCESS_REQUEST_APPROVAL_OPENED
        )
        expected_personalisation = default_personalisation() | {
            "user_type": "agent",
            "icms_url": get_importer_site_domain(),
        }
        emails.send_approval_request_opened_email(iar_approval)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.importer_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_approval_request_completed_email(self, exporter_access_request):
        ear = get_linked_access_request(exporter_access_request, self.exporter)
        ear_approval = add_approval_request(ear, self.ilb_admin_user, self.exporter_user)
        exp_template_id = get_gov_notify_template_id(EmailTypes.ACCESS_REQUEST_APPROVAL_COMPLETE)
        expected_personalisation = default_personalisation() | {
            "user_type": "user",
            "icms_url": get_caseworker_site_domain(),
        }
        emails.send_approval_request_completed_email(ear_approval)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 2
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_two_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_stopped_email(self, completed_cfs_app):
        exp_template_id = get_gov_notify_template_id(EmailTypes.APPLICATION_STOPPED)
        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_cfs_app, get_exporter_site_domain()),
            "icms_url": get_exporter_site_domain(),
        }
        emails.send_application_stopped_email(completed_cfs_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "E1_main_contact@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_reopened_email(self, completed_cfs_app):
        exp_template_id = get_gov_notify_template_id(EmailTypes.APPLICATION_REOPENED)
        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_cfs_app, get_exporter_site_domain()),
            "icms_url": get_exporter_site_domain(),
        }
        emails.send_application_reopened_email(completed_cfs_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "E1_main_contact@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    @pytest.mark.parametrize(
        "comment,expected_comment",
        [
            ("Reassigned this case to you.", "Reassigned this case to you."),
            ("", "None provided."),
        ],
    )
    def test_send_application_reassigned_email(
        self, com_app_submitted, ilb_admin_two, comment, expected_comment
    ):
        com_app_submitted.case_owner = ilb_admin_two
        com_app_submitted.save()
        exp_template_id = get_gov_notify_template_id(EmailTypes.APPLICATION_REASSIGNED)
        expected_personalisation = default_personalisation() | {
            "reference": com_app_submitted.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(com_app_submitted, get_caseworker_site_domain()),
            "comment": expected_comment,
            "icms_url": get_caseworker_site_domain(),
        }

        emails.send_application_reassigned_email(com_app_submitted, comment)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "ilb_admin_two@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_refused_email(self, fa_sil_app_submitted):
        fa_sil_app_submitted.decision = fa_sil_app_submitted.REFUSE
        fa_sil_app_submitted.refuse_reason = "Application Incomplete"
        fa_sil_app_submitted.save()
        exp_template_id = get_gov_notify_template_id(EmailTypes.APPLICATION_REFUSED)
        expected_personalisation = default_personalisation() | {
            "reference": fa_sil_app_submitted.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(fa_sil_app_submitted, get_importer_site_domain()),
            "reason": fa_sil_app_submitted.refuse_reason,
            "icms_url": get_importer_site_domain(),
        }
        emails.send_application_refused_email(fa_sil_app_submitted)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "I1_main_contact@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_complete_email(self, completed_cfs_app):
        exp_template_id = get_gov_notify_template_id(EmailTypes.APPLICATION_COMPLETE)
        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_cfs_app, get_exporter_site_domain()),
            "icms_url": get_exporter_site_domain(),
        }
        emails.send_application_complete_email(completed_cfs_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "E1_main_contact@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_variation_complete_email(self, completed_cfs_app):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.APPLICATION_VARIATION_REQUEST_COMPLETE
        )
        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_cfs_app, get_exporter_site_domain()),
            "icms_url": get_exporter_site_domain(),
        }
        emails.send_application_variation_complete_email(completed_cfs_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "E1_main_contact@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_extension_complete_email(self, completed_cfs_app):
        exp_template_id = get_gov_notify_template_id(EmailTypes.APPLICATION_EXTENSION_COMPLETE)
        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_cfs_app, get_exporter_site_domain()),
            "icms_url": get_exporter_site_domain(),
        }
        emails.send_application_extension_complete_email(completed_cfs_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "E1_main_contact@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_withdrawal_opened_email(self, com_app_submitted):
        exp_template_id = get_gov_notify_template_id(EmailTypes.WITHDRAWAL_OPENED)
        withdrawal = com_app_submitted.withdrawals.create(
            status=WithdrawApplication.Statuses.OPEN,
            request_by=self.importer_user,
            reason="Raised in error",
        )

        expected_personalisation = default_personalisation() | {
            "reference": com_app_submitted.reference,
            "reason": "Raised in error",
            "icms_url": get_caseworker_site_domain(),
        }
        emails.send_withdrawal_email(withdrawal)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 2
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "ilb_admin_user@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "ilb_admin_two@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_withdrawal_accepted_email(self, com_app_submitted):
        exp_template_id = get_gov_notify_template_id(EmailTypes.WITHDRAWAL_ACCEPTED)
        withdrawal = com_app_submitted.withdrawals.create(
            status=WithdrawApplication.Statuses.ACCEPTED, request_by=self.exporter_user
        )

        expected_personalisation = default_personalisation() | {
            "reference": com_app_submitted.reference,
            "reason": "",
            "icms_url": get_exporter_site_domain(),
        }
        emails.send_withdrawal_email(withdrawal)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.exporter_user.email,  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_withdrawal_cancelled_email(self, com_app_submitted):
        exp_template_id = get_gov_notify_template_id(EmailTypes.WITHDRAWAL_CANCELLED)
        withdrawal = com_app_submitted.withdrawals.create(
            status=WithdrawApplication.Statuses.DELETED, request_by=self.exporter_user
        )

        expected_personalisation = default_personalisation() | {
            "reference": com_app_submitted.reference,
            "reason": "",
            "icms_url": get_caseworker_site_domain(),
        }
        emails.send_withdrawal_email(withdrawal)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 2
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_user.email,  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_two_user.email,  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_withdrawal_rejected_email(self, com_app_submitted):
        exp_template_id = get_gov_notify_template_id(EmailTypes.WITHDRAWAL_REJECTED)
        withdrawal = com_app_submitted.withdrawals.create(
            status=WithdrawApplication.Statuses.REJECTED,
            request_by=self.exporter_user,
            response="Invalid",
        )
        expected_personalisation = default_personalisation() | {
            "reference": com_app_submitted.reference,
            "reason": "",
            "reason_rejected": "Invalid",
            "icms_url": get_exporter_site_domain(),
        }
        emails.send_withdrawal_email(withdrawal)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.exporter_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_withdrawal_unsupported_status_error(self, com_app_submitted):
        withdrawal = com_app_submitted.withdrawals.create(
            status="",
            request_by=self.importer_user,
        )
        with pytest.raises(ValueError, match="Unsupported Withdrawal Status"):
            emails.send_withdrawal_email(withdrawal)
            assert self.mock_gov_notify_client.send_email_notification.call_count == 0

    def test_send_variation_request_unsupported_status_error(self, completed_cfs_app):
        vr = add_variation_request_to_app(
            completed_cfs_app,
            self.ilb_admin_user,
            status=VariationRequest.Statuses.OPEN,
        )
        with pytest.raises(ValueError, match="Unsupported Variation Request Description"):
            emails.send_variation_request_email(vr, None, completed_cfs_app)
            assert self.mock_gov_notify_client.send_email_notification.call_count == 0

    def test_send_variation_request_cancelled_email(self, completed_cfs_app):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.APPLICATION_VARIATION_REQUEST_CANCELLED
        )
        vr = add_variation_request_to_app(
            completed_cfs_app,
            self.ilb_admin_user,
            status=VariationRequest.Statuses.CANCELLED,
        )
        vr.reject_cancellation_reason = "Cancel reason"
        vr.save()

        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "reason": "Cancel reason",
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "icms_url": get_caseworker_site_domain(),
            "application_url": get_case_view_url(completed_cfs_app, get_caseworker_site_domain()),
        }
        emails.send_variation_request_email(
            vr, VariationRequestDescription.CANCELLED, completed_cfs_app
        )
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_variation_request_update_required_email(self, completed_cfs_app):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_REQUIRED
        )
        vr = add_variation_request_to_app(
            completed_cfs_app,
            self.ilb_admin_user,
            status=VariationRequest.Statuses.OPEN,
        )
        vr.update_request_reason = "Please update"
        vr.save()

        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "reason": "Please update",
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "icms_url": get_exporter_site_domain(),
            "application_url": get_case_view_url(completed_cfs_app, get_exporter_site_domain()),
        }
        emails.send_variation_request_email(
            vr, VariationRequestDescription.UPDATE_REQUIRED, completed_cfs_app
        )
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.exporter_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_variation_request_update_cancelled_email(self, completed_cfs_app):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_CANCELLED
        )
        vr = add_variation_request_to_app(
            completed_cfs_app,
            self.ilb_admin_user,
            status=VariationRequest.Statuses.OPEN,
        )

        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "icms_url": get_exporter_site_domain(),
            "application_url": get_case_view_url(completed_cfs_app, get_exporter_site_domain()),
        }
        emails.send_variation_request_email(
            vr, VariationRequestDescription.UPDATE_CANCELLED, completed_cfs_app
        )
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.exporter_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_variation_request_update_received_email(self, completed_cfs_app):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.APPLICATION_VARIATION_REQUEST_UPDATE_RECEIVED
        )
        vr = add_variation_request_to_app(
            completed_cfs_app,
            self.ilb_admin_user,
            status=VariationRequest.Statuses.OPEN,
        )

        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "icms_url": get_caseworker_site_domain(),
            "application_url": get_case_view_url(completed_cfs_app, get_caseworker_site_domain()),
        }
        emails.send_variation_request_email(
            vr, VariationRequestDescription.UPDATE_RECEIVED, completed_cfs_app
        )
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_variation_request_refused_email(self, completed_dfl_app):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.APPLICATION_VARIATION_REQUEST_REFUSED
        )
        vr = add_variation_request_to_app(
            completed_dfl_app,
            self.ilb_admin_user,
            status=VariationRequest.Statuses.OPEN,
        )
        completed_dfl_app.variation_refuse_reason = "Variation refused."
        completed_dfl_app.save()

        expected_personalisation = default_personalisation() | {
            "reference": completed_dfl_app.reference,
            "reason": "Variation refused.",
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_dfl_app, get_importer_site_domain()),
            "icms_url": get_importer_site_domain(),
        }
        emails.send_variation_request_email(
            vr, VariationRequestDescription.REFUSED, completed_dfl_app
        )
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.importer_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_firearms_supplementary_report_email(self, completed_dfl_app):
        exp_template_id = get_gov_notify_template_id(EmailTypes.FIREARMS_SUPPLEMENTARY_REPORT)
        expected_personalisation = default_personalisation() | {
            "reference": completed_dfl_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_dfl_app, get_importer_site_domain()),
            "icms_url": get_importer_site_domain(),
        }
        emails.send_firearms_supplementary_report_email(completed_dfl_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.importer_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_access_request_further_information_request_email(self, importer_access_request):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST
        )
        fir = importer_access_request.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by=self.ilb_admin_user,
            request_subject="More Information Required",
            request_detail="details",
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )

        expected_personalisation = default_personalisation() | {
            "subject": "More Information Required",
            "body": "details",
            "reference": importer_access_request.reference,
            "fir_type": "access request",
            "icms_url": get_importer_site_domain(),
        }
        emails.send_further_information_request_email(fir)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "access_request_user@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_further_information_request_email(self, com_app_submitted):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST
        )
        fir = com_app_submitted.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by=self.ilb_admin_user,
            request_subject="More Information Required",
            request_detail="details",
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )
        expected_personalisation = default_personalisation() | {
            "subject": "More Information Required",
            "body": "details",
            "fir_type": "case",
            "icms_url": get_exporter_site_domain(),
            "reference": com_app_submitted.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(com_app_submitted, get_exporter_site_domain()),
        }
        emails.send_further_information_request_email(fir)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.exporter_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_access_request_further_information_request_withdrawn_email(
        self, importer_access_request
    ):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_WITHDRAWN
        )
        fir = importer_access_request.further_information_requests.create(
            status=FurtherInformationRequest.OPEN,
            requested_by=self.ilb_admin_user,
            request_subject="More Information Required",
            request_detail="details",
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )

        expected_personalisation = default_personalisation() | {
            "subject": "More Information Required",
            "body": "details",
            "reference": importer_access_request.reference,
            "fir_type": "access request",
            "icms_url": get_importer_site_domain(),
        }
        emails.send_further_information_request_withdrawn_email(fir)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "access_request_user@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_further_information_request_withdrawn_email(self, com_app_submitted):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_WITHDRAWN
        )
        fir = com_app_submitted.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by=self.ilb_admin_user,
            request_subject="More Information Required",
            request_detail="details",
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )
        expected_personalisation = default_personalisation() | {
            "subject": "More Information Required",
            "body": "details",
            "fir_type": "case",
            "icms_url": get_exporter_site_domain(),
            "reference": com_app_submitted.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(com_app_submitted, get_exporter_site_domain()),
        }
        emails.send_further_information_request_withdrawn_email(fir)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.exporter_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_access_request_further_information_request_response_email(
        self, importer_access_request
    ):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_RESPONDED
        )
        fir = importer_access_request.further_information_requests.create(
            status=FurtherInformationRequest.OPEN,
            requested_by=self.ilb_admin_user,
            request_subject="More Information Required",
            request_detail="details",
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )

        expected_personalisation = default_personalisation() | {
            "subject": "More Information Required",
            "body": "details",
            "reference": importer_access_request.reference,
            "fir_type": "access request",
            "icms_url": get_importer_site_domain(),
        }
        emails.send_further_information_request_responded_email(fir)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_further_information_request_response_email(self, com_app_submitted):
        exp_template_id = get_gov_notify_template_id(
            EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_RESPONDED
        )
        fir = com_app_submitted.further_information_requests.create(
            status=FurtherInformationRequest.DRAFT,
            requested_by=self.ilb_admin_user,
            request_subject="More Information Required",
            request_detail="details",
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )
        expected_personalisation = default_personalisation() | {
            "subject": "More Information Required",
            "body": "details",
            "fir_type": "case",
            "icms_url": get_exporter_site_domain(),
            "reference": com_app_submitted.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(com_app_submitted, get_exporter_site_domain()),
        }
        emails.send_further_information_request_responded_email(fir)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    @mock.patch("web.mail.emails.send_application_extension_complete_email")
    @mock.patch("web.mail.emails.send_application_variation_complete_email")
    @mock.patch("web.mail.emails.send_application_complete_email")
    def test_send_completed_application_email_no_variations(
        self,
        mock_send_application_complete_email,
        mock_send_application_variation_complete_email,
        mock_send_application_extension_complete_email,
        completed_cfs_app,
    ):
        mock_send_application_variation_complete_email.return_value = None
        mock_send_application_extension_complete_email.return_value = None
        mock_send_application_complete_email.return_value = None
        emails.send_completed_application_email(completed_cfs_app)
        assert mock_send_application_complete_email.called is True
        assert mock_send_application_extension_complete_email.called is False
        assert mock_send_application_variation_complete_email.called is False

    @mock.patch("web.mail.emails.send_application_extension_complete_email")
    @mock.patch("web.mail.emails.send_application_variation_complete_email")
    @mock.patch("web.mail.emails.send_application_complete_email")
    def test_send_completed_application_extension_process_email(
        self,
        mock_send_application_complete_email,
        mock_send_application_variation_complete_email,
        mock_send_application_extension_complete_email,
        completed_cfs_app,
    ):
        add_variation_request_to_app(
            completed_cfs_app,
            self.ilb_admin_user,
            status=VariationRequest.Statuses.ACCEPTED,
            extension_flag=True,
        )

        mock_send_application_variation_complete_email.return_value = None
        mock_send_application_extension_complete_email.return_value = None
        mock_send_application_complete_email.return_value = None
        emails.send_completed_application_email(completed_cfs_app)
        assert mock_send_application_complete_email.called is False
        assert mock_send_application_extension_complete_email.called is True
        assert mock_send_application_variation_complete_email.called is False

    @mock.patch("web.mail.emails.send_application_extension_complete_email")
    @mock.patch("web.mail.emails.send_application_variation_complete_email")
    @mock.patch("web.mail.emails.send_application_complete_email")
    def test_send_completed_application_variation_process_email(
        self,
        mock_send_application_complete_email,
        mock_send_application_variation_complete_email,
        mock_send_application_extension_complete_email,
        completed_cfs_app,
    ):
        add_variation_request_to_app(
            completed_cfs_app, self.ilb_admin_user, status=VariationRequest.Statuses.ACCEPTED
        )

        mock_send_application_variation_complete_email.return_value = None
        mock_send_application_extension_complete_email.return_value = None
        mock_send_application_complete_email.return_value = None
        emails.send_completed_application_email(completed_cfs_app)
        assert mock_send_application_complete_email.called is False
        assert mock_send_application_extension_complete_email.called is False
        assert mock_send_application_variation_complete_email.called is True

    @mock.patch("web.notify.notify.send_constabulary_deactivated_firearms_notification")
    @mock.patch("web.mail.emails.send_firearms_supplementary_report_email")
    @mock.patch("web.mail.emails.send_completed_application_email")
    def test_send_completed_application_process_notifications_sil(
        self, app_approved_mock, supplementary_report_mock, constabulary_mock, completed_sil_app
    ):
        app = completed_sil_app
        emails.send_completed_application_process_notifications(app)

        app_approved_mock.assert_called_with(app)
        supplementary_report_mock.assert_called_with(app)
        constabulary_mock.assert_not_called()

    @mock.patch("web.notify.notify.send_constabulary_deactivated_firearms_notification")
    @mock.patch("web.mail.emails.send_firearms_supplementary_report_email")
    @mock.patch("web.mail.emails.send_completed_application_email")
    def test_send_completed_application_process_notifications_dfl(
        self, app_approved_mock, supplementary_report_mock, constabulary_mock, completed_dfl_app
    ):
        app = completed_dfl_app
        emails.send_completed_application_process_notifications(app)

        app_approved_mock.assert_called_with(app)
        supplementary_report_mock.assert_called_with(app)
        constabulary_mock.assert_called_with(app)

    def test_send_licence_revoked_email(self, completed_dfl_app):
        document_pack.pack_active_revoke(completed_dfl_app, "TEST", True)
        pack = document_pack.pack_revoked_get(completed_dfl_app)
        expected_licence_number = document_pack.doc_ref_licence_get(pack).reference

        exp_template_id = get_gov_notify_template_id(EmailTypes.LICENCE_REVOKED)
        expected_personalisation = default_personalisation() | {
            "reference": completed_dfl_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_dfl_app, get_importer_site_domain()),
            "icms_url": get_importer_site_domain(),
            "licence_number": expected_licence_number,
        }
        emails.send_licence_revoked_email(completed_dfl_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.importer_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_certificate_revoked_email(self, completed_cfs_app):
        document_pack.pack_active_revoke(completed_cfs_app, "TEST", True)
        year = timezone.now().year

        exp_template_id = get_gov_notify_template_id(EmailTypes.CERTIFICATE_REVOKED)
        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_cfs_app, get_exporter_site_domain()),
            "icms_url": get_exporter_site_domain(),
            "certificate_references": f"CFS/{year}/00001,CFS/{year}/00002",
        }
        emails.send_certificate_revoked_email(completed_cfs_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.exporter_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_application_update_response_email(self, completed_dfl_app):
        exp_template_id = get_gov_notify_template_id(EmailTypes.APPLICATION_UPDATE_RESPONSE)
        expected_personalisation = default_personalisation() | {
            "reference": completed_dfl_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_dfl_app, get_importer_site_domain()),
            "icms_url": get_importer_site_domain(),
        }
        emails.send_application_update_response_email(completed_dfl_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_update_email(self, wood_app_submitted):
        exp_template_id = get_gov_notify_template_id(EmailTypes.APPLICATION_UPDATE)
        update_request = UpdateRequest.objects.create(
            request_detail="Update details", request_subject="Application Update"
        )
        wood_app_submitted.update_requests.add(update_request)
        expected_personalisation = default_personalisation() | {
            "subject": "Application Update",
            "body": "Update details",
            "reference": wood_app_submitted.reference,
            "icms_url": get_importer_site_domain(),
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(wood_app_submitted, get_importer_site_domain()),
        }
        emails.send_application_update_email(update_request)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.importer_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    @pytest.mark.parametrize(
        "authority_class,authority_type,expected_view_name",
        [
            (Section5Authority, "Section 5", "importer-section5-view"),
            (FirearmsAuthority, "Firearms", "importer-firearms-view"),
        ],
    )
    @freezegun.freeze_time("2020-01-01 12:00:00")
    def test_send_archived_authority_email(
        self, authority_class, authority_type, expected_view_name
    ):
        exp_template_id = get_gov_notify_template_id(EmailTypes.AUTHORITY_ARCHIVED)
        authority = authority_class.objects.create(
            importer=self.importer,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            archive_reason=["REVOKED", "WITHDRAWN"],
            other_archive_reason="Moved",
            reference=f"Test {authority_type} Authority",
        )
        expected_personalisation = default_personalisation() | {
            "reason": "Revoked\r\nWithdrawn",
            "reason_other": "Moved",
            "authority_name": authority.reference,
            "authority_type": authority_type,
            "authority_url": urljoin(
                get_caseworker_site_domain(),
                reverse(expected_view_name, kwargs={"pk": authority.pk}),
            ),
            "date": "1 January 2020",
            "icms_url": get_caseworker_site_domain(),
            "importer_name": self.importer.name,
            "importer_url": urljoin(
                get_caseworker_site_domain(),
                reverse("importer-view", kwargs={"pk": self.importer.pk}),
            ),
        }
        emails.send_authority_archived_email(authority)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 2
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            self.ilb_admin_user.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )
