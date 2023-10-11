from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest import mock

import pytest
from django.urls import reverse

from web.mail.constants import EmailTypes
from web.mail.url_helpers import get_case_view_url, get_validate_digital_signatures_url
from web.models import FurtherInformationRequest
from web.sites import get_exporter_site_domain, get_importer_site_domain
from web.tests.auth import AuthTestCase
from web.tests.helpers import CaseURLS, check_gov_notify_email_was_sent

if TYPE_CHECKING:
    from django.test.client import Client

    from web.models import Process


def _create_fir(
    process: "Process", ilb_admin_client: "Client", case_type: str, subject: str = "test_subject"
):
    if case_type in ["export", "import"]:
        ilb_admin_client.post(CaseURLS.take_ownership(process.pk, case_type))

    resp = ilb_admin_client.post(CaseURLS.add_fir(process.pk, case_type))

    with mock.patch(
        "web.domains.case.views.views_fir.send_further_information_request_email"
    ) as mock_send_email:
        mock_send_email.return_value = None
        ilb_admin_client.post(
            resp.url,
            {
                "request_subject": subject,
                "request_detail": "test request detail",
                "send": "",
            },
        )
        assert mock_send_email.called is True

    return FurtherInformationRequest.objects.get(request_subject=subject)


class TestImporterAccessRequestFIRView(AuthTestCase):
    @pytest.fixture
    def setup_process(self, importer_access_request):
        self.process = importer_access_request
        self.process.link = self.importer
        self.process.submitted_by = self.importer_user
        self.process.save()
        self.case_type = "access"
        self.fir_type = "access request"
        self.client = self.importer_client
        self.expected_site = get_importer_site_domain()

    @pytest.fixture(autouse=True)
    def setup(self, _setup, setup_process):
        self.url = reverse(
            "case:list-firs",
            kwargs={"application_pk": self.process.pk, "case_type": self.case_type},
        )

    def test_forbidden_access(self):
        response = self.ilb_admin_client.get(self.url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_authorized_access(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK

    def test_open_fir(self):
        if self.case_type in ["import", "export"]:
            self.ilb_admin_client.post(CaseURLS.take_ownership(self.process.pk, self.case_type))
        add_fir_response = self.ilb_admin_client.post(
            CaseURLS.add_fir(self.process.pk, self.case_type),
        )
        assert add_fir_response.status_code == HTTPStatus.FOUND

        response = self.ilb_admin_client.post(
            add_fir_response.url,
            data={
                "request_subject": "open fir",
                "request_detail": "test request detail",
                "send": "",
            },
            follow=True,
        )
        assert response.status_code == HTTPStatus.OK
        fir_list = response.context["firs"]
        assert len(fir_list) == 1
        self.assert_request_email_sent()

    def assert_request_email_sent(self):
        check_gov_notify_email_was_sent(
            1,
            [self.process.submitted_by.email],
            EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST,
            self.expected_email_personalisation(),
            exp_subject="open fir",
            exp_in_body="test request detail",
        )

    def expected_email_personalisation(self):
        return {
            "reference": self.process.reference,
            "icms_url": self.expected_site,
            "fir_type": self.fir_type,
        }

    def test_deleted_firs(self):
        fir = _create_fir(self.process, self.ilb_admin_client, self.case_type, "test delete")
        assert fir.status == FurtherInformationRequest.OPEN

        response = self.client.get(self.url)
        fir_list = response.context["firs"]
        assert len(fir_list) == 1
        assert fir_list.first() == fir

        self.ilb_admin_client.post(CaseURLS.delete_fir(self.process.pk, fir.pk, self.case_type))

        response = self.client.get(self.url)

        fir_list = response.context["firs"]
        assert len(fir_list) == 0
        fir.refresh_from_db()
        assert fir.status == FurtherInformationRequest.DELETED

    def test_withdraw_firs(self):
        fir = _create_fir(self.process, self.ilb_admin_client, self.case_type, "test withdraw")
        assert fir.status == FurtherInformationRequest.OPEN

        response = self.client.get(self.url)

        fir_list = response.context["firs"]
        assert fir_list.first() == fir

        self.ilb_admin_client.post(CaseURLS.withdraw_fir(self.process.pk, fir.pk, self.case_type))

        response = self.client.get(self.url)

        fir_list = response.context["firs"]
        assert len(fir_list) == 0
        fir.refresh_from_db()
        assert fir.status == FurtherInformationRequest.DRAFT
        self.assert_withdrawn_email_sent()

    def assert_withdrawn_email_sent(self):
        check_gov_notify_email_was_sent(
            1,
            [self.process.submitted_by.email],
            EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_WITHDRAWN,
            self.expected_email_personalisation(),
            exp_subject="test withdraw",
            exp_in_body="test request detail",
        )

    def test_respond_to_firs(self):
        fir = _create_fir(
            self.process, self.ilb_admin_client, self.case_type, "test responded email"
        )
        response = self.client.post(
            CaseURLS.respond_to_fir(self.process.pk, fir.pk, self.case_type),
            data={"response_detail": "Thanks"},
        )
        assert response.status_code == HTTPStatus.FOUND

        response = self.client.get(self.url)

        fir_list = response.context["firs"]

        assert len(fir_list) == 1
        actual_firs = fir_list.first()
        assert actual_firs.status == FurtherInformationRequest.RESPONDED
        assert actual_firs.response_detail == "Thanks"
        self.assert_response_email_sent()

    def assert_response_email_sent(self):
        check_gov_notify_email_was_sent(
            1,
            [self.ilb_admin_user.email],
            EmailTypes.ACCESS_REQUEST_FURTHER_INFORMATION_REQUEST_RESPONDED,
            self.expected_email_personalisation(),
            exp_subject="test responded email",
            exp_in_body="test request detail",
        )

    def test_close_firs(self):
        fir = _create_fir(self.process, self.ilb_admin_client, self.case_type, "test withdraw")
        fir.status = FurtherInformationRequest.RESPONDED
        fir.response_detail = "OK"
        fir.save()

        response = self.ilb_admin_client.post(
            CaseURLS.close_fir(self.process.pk, fir.pk, self.case_type),
        )
        assert response.status_code == HTTPStatus.FOUND

        response = self.client.get(self.url)

        fir_list = response.context["firs"]
        assert len(fir_list) == 1
        assert fir_list.first() == fir

        fir.refresh_from_db()
        assert fir.status == FurtherInformationRequest.CLOSED


class TestExportAccessRequestFIRView(TestImporterAccessRequestFIRView):
    @pytest.fixture
    def setup_process(self, exporter_access_request):
        self.process = exporter_access_request
        self.process.link = self.exporter
        self.process.submitted_by = self.exporter_user
        self.process.save()
        self.case_type = "access"
        self.fir_type = "access request"
        self.client = self.exporter_client
        self.expected_site = get_exporter_site_domain()


class TestExportApplicationFIRView(TestImporterAccessRequestFIRView):
    @pytest.fixture
    def setup_process(self, cfs_app_submitted):
        self.process = cfs_app_submitted
        self.process.link = self.exporter
        self.process.submitted_by = self.exporter_user
        self.process.save()

        self.case_type = "export"
        self.fir_type = "case"
        self.client = self.exporter_client
        self.expected_site = get_exporter_site_domain()

    def assert_request_email_sent(self):
        check_gov_notify_email_was_sent(
            1,
            [self.process.submitted_by.email],
            EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST,
            self.expected_email_personalisation(),
            exp_subject="open fir",
            exp_in_body="test request detail",
        )

    def assert_response_email_sent(self):
        check_gov_notify_email_was_sent(
            1,
            [self.ilb_admin_user.email],
            EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_RESPONDED,
            self.expected_email_personalisation(),
            exp_subject="test responded email",
            exp_in_body="test request detail",
        )

    def assert_withdrawn_email_sent(self):
        check_gov_notify_email_was_sent(
            1,
            [self.process.submitted_by.email],
            EmailTypes.APPLICATION_FURTHER_INFORMATION_REQUEST_WITHDRAWN,
            self.expected_email_personalisation(),
            exp_subject="test withdraw",
            exp_in_body="test request detail",
        )

    def expected_email_personalisation(self):
        return {
            "reference": self.process.reference,
            "icms_url": self.expected_site,
            "fir_type": self.fir_type,
            "validate_digital_signatures_url": get_validate_digital_signatures_url(full_url=True),
            "application_url": get_case_view_url(self.process, self.expected_site),
        }


class TestImportApplicationFIRView(TestExportApplicationFIRView):
    @pytest.fixture
    def setup_process(self, sanctions_app_submitted):
        self.process = sanctions_app_submitted
        self.process.link = self.importer
        self.process.submitted_by = self.importer_user
        self.process.save()

        self.case_type = "import"
        self.fir_type = "case"
        self.client = self.importer_client
        self.expected_site = get_importer_site_domain()
