from datetime import datetime

import pytest

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.mail.constants import EmailTypes
from web.mail.emails import create_case_email, send_case_email
from web.models import FurtherInformationRequest, UpdateRequest, VariationRequest
from web.reports.interfaces import IssuedCertificateReportInterface
from web.tests.helpers import add_variation_request_to_app

EXPECTED_HEADER = [
    "Certificate Reference",
    "Case Reference",
    "Application Type",
    "Submitted Datetime",
    "Issue Datetime",
    "Case Processing Time",
    "Total Processing Time",
    "Exporter",
    "Contact Full Name",
    "Agent",
    "Country",
    "Is Manufacturer",
    "Responsible Person Statement",
    "Countries of Manufacture",
    "Product Legislation",
    "HSE Email Count",
    "BEIS Email Count",
    "Application Update Count",
    "FIR Count",
    "Business Days to Process",
]


class TestIssuedCertificateReportInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user):
        self.report_schedule = report_schedule
        self.ilb_admin_user = ilb_admin_user

    def _setup_app_with_variation_request(self, app: ImpOrExp) -> None:
        document_pack.pack_draft_create(app)
        add_variation_request_to_app(
            app, self.ilb_admin_user, status=VariationRequest.Statuses.OPEN
        )
        app.status = ImpExpStatus.VARIATION_REQUESTED
        app.save()

    def _setup_app_with_update_request(self, app: ImpOrExp, status: UpdateRequest.Status) -> None:
        update_request = UpdateRequest.objects.create(
            status=status,
        )
        app.update_requests.add(update_request)

    def _setup_app_with_case_email(
        self, app: ImpOrExp, email_type: EmailTypes, completed: bool
    ) -> None:
        case_email = create_case_email(app, email_type)
        if completed:
            send_case_email(case_email)
        app.case_emails.add(case_email)

    def _setup_app_with_fir(self, app: ImpOrExp) -> None:
        app.further_information_requests.create(
            status=FurtherInformationRequest.CLOSED,
            requested_by=self.ilb_admin_user,
            request_subject="subject",
            request_detail="body",
            process_type=FurtherInformationRequest.PROCESS_TYPE,
        )

    def _setup_app_update_submitted_and_completed_dates(self, app):
        app.submit_datetime = datetime(2024, 1, 1, 12, 0, 0)
        app.save()
        for cert in app.certificates.all():
            cert.case_completion_datetime = datetime(2024, 1, 9, 13, 7, 0)
            cert.save()

    def test_issued_certificate_report_interface_get_data_header(self):
        interface = IssuedCertificateReportInterface(self.report_schedule)
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_HEADER,
            "results": [],
        }

    def test_issued_certificate_report_interface_get_data_cfs(self, completed_cfs_app):
        self._setup_app_with_variation_request(completed_cfs_app)
        self._setup_app_update_submitted_and_completed_dates(completed_cfs_app)
        self._setup_app_with_case_email(completed_cfs_app, EmailTypes.HSE_CASE_EMAIL, True)
        interface = IssuedCertificateReportInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Agent": "",
                "Application Type": "Certificate of Free Sale",
                "Application Update Count": 0,
                "BEIS Email Count": 0,
                "Business Days to Process": 7,
                "Case Processing Time": "8d 1h 7m",
                "Case Reference": "CA/2024/00001",
                "Certificate Reference": "CFS/2024/00002",
                "Contact Full Name": "E1_main_contact_first_name E1_main_contact_last_name",
                "Countries of Manufacture": "Afghanistan",
                "Country": "Zimbabwe",
                "Exporter": "Test Exporter 1",
                "FIR Count": 0,
                "HSE Email Count": 1,
                "Is Manufacturer": "Yes",
                "Issue Datetime": "09/01/2024 13:07:00",
                "Product Legislation": "Biocide Products Regulation 528/2012 as retained in UK law",
                "Responsible Person Statement": "Yes",
                "Submitted Datetime": "01/01/2024 12:00:00",
                "Total Processing Time": "8d 1h 7m",
            },
            {
                "Agent": "",
                "Application Type": "Certificate of Free Sale",
                "Application Update Count": 0,
                "BEIS Email Count": 0,
                "Business Days to Process": 7,
                "Case Processing Time": "8d 1h 7m",
                "Case Reference": "CA/2024/00001",
                "Certificate Reference": "CFS/2024/00001",
                "Contact Full Name": "E1_main_contact_first_name E1_main_contact_last_name",
                "Countries of Manufacture": "Afghanistan",
                "Country": "Afghanistan",
                "Exporter": "Test Exporter 1",
                "FIR Count": 0,
                "HSE Email Count": 1,
                "Is Manufacturer": "Yes",
                "Issue Datetime": "09/01/2024 13:07:00",
                "Product Legislation": "Biocide Products Regulation 528/2012 as retained in UK law",
                "Responsible Person Statement": "Yes",
                "Submitted Datetime": "01/01/2024 12:00:00",
                "Total Processing Time": "8d 1h 7m",
            },
        ]

    def test_issued_certificate_report_interface_get_data_gmp(self, completed_gmp_app):
        self._setup_app_update_submitted_and_completed_dates(completed_gmp_app)
        self._setup_app_with_case_email(completed_gmp_app, EmailTypes.BEIS_CASE_EMAIL, False)
        self._setup_app_with_case_email(completed_gmp_app, EmailTypes.BEIS_CASE_EMAIL, True)
        self._setup_app_with_case_email(completed_gmp_app, EmailTypes.BEIS_CASE_EMAIL, True)
        interface = IssuedCertificateReportInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Agent": "",
                "Application Type": "Certificate of Good Manufacturing Practice",
                "Application Update Count": 0,
                "BEIS Email Count": 2,
                "Business Days to Process": 7,
                "Case Processing Time": "8d 1h 7m",
                "Case Reference": "GA/2024/00001",
                "Certificate Reference": "GMP/2024/00001",
                "Contact Full Name": "E1_main_contact_first_name E1_main_contact_last_name",
                "Countries of Manufacture": "",
                "Country": "China",
                "Exporter": "Test Exporter 1",
                "FIR Count": 0,
                "HSE Email Count": 0,
                "Is Manufacturer": "",
                "Issue Datetime": "09/01/2024 13:07:00",
                "Product Legislation": "",
                "Responsible Person Statement": "",
                "Submitted Datetime": "01/01/2024 12:00:00",
                "Total Processing Time": "8d 1h 7m",
            },
        ]

    def test_issued_certificate_report_interface_get_data_com(
        self, completed_com_app, ilb_admin_client
    ):
        self._setup_app_update_submitted_and_completed_dates(completed_com_app)
        self._setup_app_with_fir(completed_com_app)
        self._setup_app_with_update_request(completed_com_app, UpdateRequest.Status.DRAFT)
        self._setup_app_with_update_request(completed_com_app, UpdateRequest.Status.CLOSED)
        interface = IssuedCertificateReportInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Agent": "",
                "Application Type": "Certificate of Manufacture",
                "Application Update Count": 1,
                "BEIS Email Count": 0,
                "Business Days to Process": 7,
                "Case Processing Time": "8d 1h 7m",
                "Case Reference": "CA/2024/00001",
                "Certificate Reference": "COM/2024/00001",
                "Contact Full Name": "E1_main_contact_first_name E1_main_contact_last_name",
                "Countries of Manufacture": "",
                "Country": "Afghanistan",
                "Exporter": "Test Exporter 1",
                "FIR Count": 1,
                "HSE Email Count": 0,
                "Is Manufacturer": "",
                "Issue Datetime": "09/01/2024 13:07:00",
                "Product Legislation": "",
                "Responsible Person Statement": "",
                "Submitted Datetime": "01/01/2024 12:00:00",
                "Total Processing Time": "8d 1h 7m",
            },
        ]
