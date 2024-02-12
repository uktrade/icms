from datetime import datetime

import pytest
from django.utils.timezone import make_aware
from freezegun import freeze_time

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.mail.constants import EmailTypes
from web.mail.emails import create_case_email, send_case_email
from web.models import (
    ExporterAccessRequest,
    FurtherInformationRequest,
    ImporterAccessRequest,
    Task,
    UpdateRequest,
    VariationRequest,
)
from web.reports.interfaces import (
    AccessRequestTotalsInterface,
    ExporterAccessRequestInterface,
    ImporterAccessRequestInterface,
    ImportLicenceInterface,
    IssuedCertificateReportInterface,
)
from web.tests.helpers import add_variation_request_to_app

EXPECTED_IMPORT_ACCESS_REQUEST_HEADER = [
    "Request Date",
    "Request Type",
    "Importer Name",
    "Importer Address",
    "Agent Name",
    "Agent Address",
    "Response",
    "Response Reason",
]

EXPECTED_EXPORT_ACCESS_REQUEST_HEADER = [
    "Request Date",
    "Request Type",
    "Exporter Name",
    "Exporter Address",
    "Agent Name",
    "Agent Address",
    "Response",
    "Response Reason",
]

EXPECTED_ACCESS_REQUEST_TOTALS_HEADER = [
    "Total Requests",
    "Approved Requests",
    "Refused Requests",
]

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

EXPECTED_IMPORT_LICENCE_HEADER = [
    "Case Ref",
    "Licence Ref",
    "Licence Type",
    "Under Appeal",
    "Ima Type",
    "Ima Type Title",
    "Ima Sub Type",
    "Variation No",
    "Status",
    "Ima Sub Type Title",
    "Importer Name",
    "Agent Name",
    "App Contact Name",
    "Coo Country Name",
    "Coc Country Name",
    "Shipping Year",
    "Com Group Name",
    "Commodity Codes",
    "Initial Submitted Datetime",
    "Initial Case Closed Datetime",
    "Time to Initial Close",
    "Latest Case Closed Datetime",
    "Licence Dates",
    "Licence Start Date",
    "Licence End Date",
    "Importer Printable",
]


@pytest.fixture
@freeze_time("2021-02-01 12:00:00")
def approved_importer_access_request(importer_access_request):
    importer_access_request.response = ImporterAccessRequest.APPROVED
    importer_access_request.save()


@pytest.fixture
@freeze_time("2021-02-11 12:00:00")
def refused_importer_access_request(report_user):
    iar = ImporterAccessRequest.objects.create(
        process_type=ImporterAccessRequest.PROCESS_TYPE,
        request_type=ImporterAccessRequest.AGENT_ACCESS,
        status=ImporterAccessRequest.Statuses.CLOSED,
        response=ImporterAccessRequest.REFUSED,
        submitted_by=report_user,
        last_updated_by=report_user,
        reference="iar/2",
        organisation_name="Import Ltd",
        organisation_address="1 Main Street",
        agent_name="Test Agent",
        agent_address="1 Agent House",
        response_reason="Test refusing request",
    )
    iar.tasks.create(is_active=True, task_type=Task.TaskType.PROCESS)


@pytest.fixture
@freeze_time("2021-02-01 12:00:00")
def approved_exporter_access_request(exporter_access_request):
    exporter_access_request.response = ExporterAccessRequest.APPROVED
    exporter_access_request.save()


@pytest.fixture
@freeze_time("2021-02-11 12:00:00")
def refused_exporter_access_request(report_user):
    ear = ExporterAccessRequest.objects.create(
        process_type=ExporterAccessRequest.PROCESS_TYPE,
        request_type=ExporterAccessRequest.AGENT_ACCESS,
        status=ExporterAccessRequest.Statuses.CLOSED,
        response=ExporterAccessRequest.REFUSED,
        submitted_by=report_user,
        last_updated_by=report_user,
        reference="ear/2",
        organisation_name="Export Ltd",
        organisation_address="2 Main Street",
        agent_name="Test Agent",
        agent_address="2 Agent House",
        response_reason="Test refusing request",
    )
    ear.tasks.create(is_active=True, task_type=Task.TaskType.PROCESS)


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
        app.submit_datetime = make_aware(datetime(2024, 1, 1, 12, 0, 0))
        app.save()
        for cert in app.certificates.all():
            cert.case_completion_datetime = make_aware(datetime(2024, 1, 9, 13, 7, 0))
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


class TestImporterAccessRequestInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user):
        self.report_schedule = report_schedule
        self.ilb_admin_user = ilb_admin_user

    def test_get_data_header(self):
        interface = ImporterAccessRequestInterface(self.report_schedule)
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_IMPORT_ACCESS_REQUEST_HEADER,
            "results": [],
        }

    def test_get_data_results(
        self, approved_importer_access_request, refused_importer_access_request
    ):
        interface = ImporterAccessRequestInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Agent Address": "1 Agent House",
                "Agent Name": "Test Agent",
                "Importer Address": "1 Main Street",
                "Importer Name": "Import Ltd",
                "Request Date": "11/02/2021",
                "Request Type": "Agent Importer Access Request",
                "Response": "Refused",
                "Response Reason": "Test refusing request",
            },
            {
                "Agent Address": "",
                "Agent Name": "",
                "Importer Address": "1 Main Street",
                "Importer Name": "Import Ltd",
                "Request Date": "01/02/2021",
                "Request Type": "Importer Access Request",
                "Response": "Approved",
                "Response Reason": "",
            },
        ]


class TestExporterAccessRequestInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user):
        self.report_schedule = report_schedule
        self.ilb_admin_user = ilb_admin_user

    def test_get_data_header(self, exporter_access_request):
        interface = ExporterAccessRequestInterface(self.report_schedule)
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_EXPORT_ACCESS_REQUEST_HEADER,
            "results": [],
        }

    def test_get_data_results(
        self, approved_exporter_access_request, refused_exporter_access_request
    ):
        interface = ExporterAccessRequestInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Agent Address": "2 Agent House",
                "Agent Name": "Test Agent",
                "Exporter Address": "2 Main Street",
                "Exporter Name": "Export Ltd",
                "Request Date": "11/02/2021",
                "Request Type": "Agent Exporter Access Request",
                "Response": "Refused",
                "Response Reason": "Test refusing request",
            },
            {
                "Agent Address": "",
                "Agent Name": "",
                "Exporter Address": "2 Main Street",
                "Exporter Name": "Export Ltd",
                "Request Date": "01/02/2021",
                "Request Type": "Exporter Access Request",
                "Response": "Approved",
                "Response Reason": "",
            },
        ]


class TestAccessRequestTotalsInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user):
        self.report_schedule = report_schedule
        self.ilb_admin_user = ilb_admin_user

    def test_get_data(
        self,
        approved_importer_access_request,
        approved_exporter_access_request,
        refused_importer_access_request,
        refused_exporter_access_request,
    ):
        interface = AccessRequestTotalsInterface(self.report_schedule)
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_ACCESS_REQUEST_TOTALS_HEADER,
            "results": [{"Approved Requests": 2, "Refused Requests": 2, "Total Requests": 4}],
        }


class TestImportLicenceInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user):
        self.report_schedule = report_schedule
        self.ilb_admin_user = ilb_admin_user

    def test_get_data_header(self):
        interface = ImportLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_IMPORT_LICENCE_HEADER,
            "results": [],
        }

    def test_get_data_dfl(self, completed_dfl_app):
        interface = ImportLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Case Ref": "IMA/2024/00001",
                "Licence Ref": "GBSIL0000001B",
                "Licence Type": "Electronic",
                "Under Appeal": "",
                "Ima Type": "FA",
                "Ima Type Title": "Firearms and Ammunition",
                "Ima Sub Type": "DEACTIVATED",
                "Variation No": 0,
                "Status": "COMPLETED",
                "Ima Sub Type Title": "Deactivated Firearms Import Licence",
                "Importer Name": "Test Importer 1",
                "Agent Name": "",
                "App Contact Name": "I1_main_contact_first_name I1_main_contact_last_name",
                "Coo Country Name": "Afghanistan",
                "Coc Country Name": "Albania",
                "Shipping Year": "",
                "Com Group Name": "",
                "Commodity Codes": "",
                "Initial Submitted Datetime": "01/01/2024 12:00:00",
                "Initial Case Closed Datetime": "02/01/2024 17:02:00",
                "Time to Initial Close": "1d 5h 2m",
                "Latest Case Closed Datetime": "02/01/2024 17:02:00",
                "Licence Dates": "01 Jun 2020 - 31 Dec 2024",
                "Licence Start Date": "01/06/2020",
                "Licence End Date": "31/12/2024",
                "Importer Printable": False,
            }
        ]

    def test_get_data_sil(self, completed_sil_app):
        interface = ImportLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Case Ref": "IMA/2024/00001",
                "Licence Ref": "GBSIL0000001B",
                "Licence Type": "Electronic",
                "Under Appeal": "",
                "Ima Type": "FA",
                "Ima Type Title": "Firearms and Ammunition",
                "Ima Sub Type": "SIL",
                "Variation No": 0,
                "Status": "COMPLETED",
                "Ima Sub Type Title": "Specific Individual Import Licence",
                "Importer Name": "Test Importer 1",
                "Agent Name": "",
                "App Contact Name": "I1_main_contact_first_name I1_main_contact_last_name",
                "Coo Country Name": "Afghanistan",
                "Coc Country Name": "Afghanistan",
                "Shipping Year": "",
                "Com Group Name": "",
                "Commodity Codes": "",
                "Initial Submitted Datetime": "01/01/2024 12:00:00",
                "Initial Case Closed Datetime": "02/01/2024 17:02:00",
                "Time to Initial Close": "1d 5h 2m",
                "Latest Case Closed Datetime": "02/01/2024 17:02:00",
                "Licence Dates": "01 Jun 2020 - 31 Dec 2024",
                "Licence Start Date": "01/06/2020",
                "Licence End Date": "31/12/2024",
                "Importer Printable": False,
            }
        ]

    def test_get_data_oil(self, completed_oil_app):
        interface = ImportLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Case Ref": "IMA/2024/00001",
                "Licence Ref": "GBOIL0000001B",
                "Licence Type": "Electronic",
                "Under Appeal": "",
                "Ima Type": "FA",
                "Ima Type Title": "Firearms and Ammunition",
                "Ima Sub Type": "OIL",
                "Variation No": 0,
                "Status": "COMPLETED",
                "Ima Sub Type Title": "Open Individual Import Licence",
                "Importer Name": "Test Importer 1",
                "Agent Name": "",
                "App Contact Name": "I1_main_contact_first_name I1_main_contact_last_name",
                "Coo Country Name": "Any Country",
                "Coc Country Name": "Any Country",
                "Shipping Year": "",
                "Com Group Name": "",
                "Commodity Codes": "",
                "Initial Submitted Datetime": "01/01/2024 12:00:00",
                "Initial Case Closed Datetime": "02/01/2024 17:02:00",
                "Time to Initial Close": "1d 5h 2m",
                "Latest Case Closed Datetime": "02/01/2024 17:02:00",
                "Licence Dates": "01 Jun 2020 - 31 Dec 2024",
                "Licence Start Date": "01/06/2020",
                "Licence End Date": "31/12/2024",
                "Importer Printable": False,
            }
        ]

    def test_get_data_wood(self, completed_wood_app):
        interface = ImportLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Case Ref": "IMA/2024/00001",
                "Licence Ref": "0000001B",
                "Licence Type": "Paper",
                "Under Appeal": "",
                "Ima Type": "WD",
                "Ima Type Title": "Wood (Quota)",
                "Ima Sub Type": "QUOTA",
                "Variation No": 0,
                "Status": "COMPLETED",
                "Ima Sub Type Title": "QUOTA",
                "Importer Name": "Test Importer 1",
                "Agent Name": "",
                "App Contact Name": "I1_main_contact_first_name I1_main_contact_last_name",
                "Coo Country Name": "",
                "Coc Country Name": "",
                "Shipping Year": 2024,
                "Com Group Name": "",
                "Commodity Codes": "",
                "Initial Submitted Datetime": "01/01/2024 12:00:00",
                "Initial Case Closed Datetime": "02/01/2024 17:02:00",
                "Time to Initial Close": "1d 5h 2m",
                "Latest Case Closed Datetime": "02/01/2024 17:02:00",
                "Licence Dates": "01 Jun 2020 - 31 Dec 2024",
                "Licence Start Date": "01/06/2020",
                "Licence End Date": "31/12/2024",
                "Importer Printable": False,
            }
        ]

    def test_get_data_sps(self, completed_sps_app):
        interface = ImportLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Case Ref": "IMA/2024/00001",
                "Licence Ref": "GBAOG0000001B",
                "Licence Type": "Electronic",
                "Under Appeal": "",
                "Ima Type": "SPS",
                "Ima Type Title": "Prior Surveillance",
                "Ima Sub Type": "SPS1",
                "Variation No": 0,
                "Status": "COMPLETED",
                "Ima Sub Type Title": "SPS1",
                "Importer Name": "Test Importer 1",
                "Agent Name": "",
                "App Contact Name": "I1_main_contact_first_name I1_main_contact_last_name",
                "Coo Country Name": "Afghanistan",
                "Coc Country Name": "Armenia",
                "Shipping Year": "",
                "Com Group Name": "",
                "Commodity Codes": "Code: 111111",
                "Initial Submitted Datetime": "01/01/2024 12:00:00",
                "Initial Case Closed Datetime": "02/01/2024 17:02:00",
                "Time to Initial Close": "1d 5h 2m",
                "Latest Case Closed Datetime": "02/01/2024 17:02:00",
                "Licence Dates": "01 Jun 2020 - 31 Dec 2024",
                "Licence Start Date": "01/06/2020",
                "Licence End Date": "31/12/2024",
                "Importer Printable": True,
            }
        ]

    def test_get_data_sanctions(self, completed_sanctions_app):
        interface = ImportLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Case Ref": "IMA/2024/00001",
                "Licence Ref": "GBSAN0000001B",
                "Licence Type": "Electronic",
                "Under Appeal": "",
                "Ima Type": "ADHOC",
                "Ima Type Title": "Sanctions and Adhoc Licence Application",
                "Ima Sub Type": "ADHOC1",
                "Variation No": 0,
                "Status": "COMPLETED",
                "Ima Sub Type Title": "ADHOC1",
                "Importer Name": "Test Importer 1",
                "Agent Name": "",
                "App Contact Name": "I1_main_contact_first_name I1_main_contact_last_name",
                "Coo Country Name": "Iran",
                "Coc Country Name": "Afghanistan",
                "Shipping Year": "",
                "Com Group Name": "",
                "Commodity Codes": "Code: 7112990090; Desc: More Commoditites, Code: 2707100010; Desc: Test Goods",
                "Initial Submitted Datetime": "01/01/2024 12:00:00",
                "Initial Case Closed Datetime": "02/01/2024 17:02:00",
                "Time to Initial Close": "1d 5h 2m",
                "Latest Case Closed Datetime": "02/01/2024 17:02:00",
                "Licence Dates": "01 Jun 2020 - 31 Dec 2024",
                "Licence Start Date": "01/06/2020",
                "Licence End Date": "31/12/2024",
                "Importer Printable": False,
            }
        ]
