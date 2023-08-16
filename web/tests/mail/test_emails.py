from unittest import mock

import pytest
from django.conf import settings

from web.mail import emails
from web.mail.constants import EmailTypes
from web.mail.url_helpers import get_case_view_url, get_validate_digital_signatures_url
from web.models import EmailTemplate, ImporterAccessRequest, VariationRequest
from web.tests.auth.auth import AuthTestCase
from web.tests.helpers import add_variation_request_to_app


def default_personalisation() -> dict:
    return {
        "icms_url": settings.DEFAULT_DOMAIN,
        "icms_contact_email": settings.ILB_CONTACT_EMAIL,
        "icms_contact_phone": settings.ILB_CONTACT_PHONE,
        "subject": "",
        "body": "",
    }


class TestEmails(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, mock_gov_notify_client):
        self.mock_gov_notify_client = mock_gov_notify_client

    def test_access_request_email(self, importer_access_request):
        exp_template_id = str(
            EmailTemplate.objects.get(name=EmailTypes.ACCESS_REQUEST).gov_notify_template_id
        )
        expected_personalisation = default_personalisation() | {
            "reference": importer_access_request.reference
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

    def test_access_request_closed_email(self, importer_access_request):
        importer_access_request.response = ImporterAccessRequest.APPROVED
        importer_access_request.request_type = ImporterAccessRequest.AGENT_ACCESS

        exp_template_id = str(
            EmailTemplate.objects.get(name=EmailTypes.ACCESS_REQUEST_CLOSED).gov_notify_template_id
        )
        expected_personalisation = default_personalisation() | {
            "agent": "Agent ",
            "organisation": "Import Ltd",
            "outcome": "Approved",
            "reason": "",
            "request_type": "Importer",
        }
        emails.send_access_request_closed_email(importer_access_request)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            importer_access_request.submitted_by.email,
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_stopped_email(self, completed_cfs_app):
        exp_template_id = str(
            EmailTemplate.objects.get(name=EmailTypes.APPLICATION_STOPPED).gov_notify_template_id
        )
        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_cfs_app, full_url=True),
        }
        emails.send_application_stopped_email(completed_cfs_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "E1_main_contact@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_complete_email(self, completed_cfs_app):
        exp_template_id = str(
            EmailTemplate.objects.get(name=EmailTypes.APPLICATION_COMPLETE).gov_notify_template_id
        )
        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_cfs_app, full_url=True),
        }
        emails.send_application_complete_email(completed_cfs_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "E1_main_contact@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_variation_complete_email(self, completed_cfs_app):
        exp_template_id = str(
            EmailTemplate.objects.get(
                name=EmailTypes.APPLICATION_VARIATION_REQUEST_COMPLETE
            ).gov_notify_template_id
        )
        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_cfs_app, full_url=True),
        }
        emails.send_application_variation_complete_email(completed_cfs_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "E1_main_contact@example.com",  # /PS-IGNORE
            exp_template_id,
            personalisation=expected_personalisation,
        )

    def test_send_application_extension_complete_email(self, completed_cfs_app):
        exp_template_id = str(
            EmailTemplate.objects.get(
                name=EmailTypes.APPLICATION_EXTENSION_COMPLETE
            ).gov_notify_template_id
        )
        expected_personalisation = default_personalisation() | {
            "reference": completed_cfs_app.reference,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(completed_cfs_app, full_url=True),
        }
        emails.send_application_extension_complete_email(completed_cfs_app)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "E1_main_contact@example.com",  # /PS-IGNORE
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
    @mock.patch("web.notify.notify.send_supplementary_report_notification")
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
    @mock.patch("web.notify.notify.send_supplementary_report_notification")
    @mock.patch("web.mail.emails.send_completed_application_email")
    def test_send_completed_application_process_notifications_dfl(
        self, app_approved_mock, supplementary_report_mock, constabulary_mock, completed_dfl_app
    ):
        app = completed_dfl_app
        emails.send_completed_application_process_notifications(app)

        app_approved_mock.assert_called_with(app)
        supplementary_report_mock.assert_called_with(app)
        constabulary_mock.assert_called_with(app)
