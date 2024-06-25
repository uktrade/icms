import datetime as dt

import pydantic
import pytest
from django.utils.timezone import make_aware
from freezegun import freeze_time

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.mail.constants import EmailTypes
from web.mail.emails import create_case_email, send_case_email
from web.models import (
    CaseEmail,
    ExporterAccessRequest,
    FurtherInformationRequest,
    ImporterAccessRequest,
    Task,
    UpdateRequest,
    VariationRequest,
)
from web.permissions import organisation_add_contact
from web.reports.interfaces import (
    AccessRequestTotalsInterface,
    ActiveUserInterface,
    DFLFirearmsLicenceInterface,
    ExporterAccessRequestInterface,
    ImporterAccessRequestInterface,
    ImportLicenceInterface,
    IssuedCertificateReportInterface,
    OILFirearmsLicenceInterface,
    SILFirearmsLicenceInterface,
    SupplementaryFirearmsInterface,
)
from web.reports.serializers import (
    AccessRequestTotalsReportSerializer,
    DFLFirearmsLicenceSerializer,
    ImporterAccessRequestReportSerializer,
    ImportLicenceSerializer,
    SupplementaryFirearmsSerializer,
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

EXPECTED_ISSUED_CERTIFICATE_HEADER = [
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
    "Continent",
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

EXPECTED_SUPPLEMENTARY_FIREARMS_HEADER = [
    "Licence Reference",
    "Case Reference",
    "Case Type",
    "Importer",
    "Eori Number",
    "Importer Address",
    "Licence Start Date",
    "Licence Expiry Date",
    "Country of Origin",
    "Country of Consignment",
    "Endorsements",
    "Constabularies",
    "Report Date",
    "Goods Description",
    "Goods Quantity",
    "Firearms Exceed Quantity",
    "Goods Description with Subsection",
    "Who Bought From Name",
    "Who Bought From Reg No",
    "Who Bought From Address",
    "Frame Serial Number",
    "Make/Model",
    "Calibre",
    "Gun Barrel Proofing meets CIP",
    "Firearms Document",
    "Date Firearms Received",
    "Means of Transport",
    "Reported all firearms for licence",
]

EXPECTED_FIREARMS_LICENCES_HEADER = [
    "Licence Reference",
    "Licence Variation Number",
    "Case Reference",
    "Importer",
    "TURN Number",
    "Importer Address",
    "First Submitted Date",
    "Final Submitted Date",
    "Licence Start Date",
    "Licence Expiry Date",
    "Country of Origin",
    "Country of Consignment",
    "Endorsements",
    "Revoked",
    "Goods Description",
]

EXPECTED_ACTIVE_USER_HEADER = [
    "First Name",  # /PS-IGNORE
    "Last Name",  # /PS-IGNORE
    "Email Address",
    "Is Importer",
    "Is Exporter",
    "Businesses",
]


@pytest.fixture
@freeze_time("2021-02-01 12:00:00")
def approved_importer_access_request(importer_access_request):
    importer_access_request.response = ImporterAccessRequest.APPROVED
    importer_access_request.save()


@pytest.fixture
@freeze_time("2021-02-11 12:00:00")
def refused_importer_access_request(ilb_admin_user):
    iar = ImporterAccessRequest.objects.create(
        process_type=ImporterAccessRequest.PROCESS_TYPE,
        request_type=ImporterAccessRequest.AGENT_ACCESS,
        status=ImporterAccessRequest.Statuses.CLOSED,
        response=ImporterAccessRequest.REFUSED,
        submitted_by=ilb_admin_user,
        last_updated_by=ilb_admin_user,
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
def refused_exporter_access_request(ilb_admin_user):
    ear = ExporterAccessRequest.objects.create(
        process_type=ExporterAccessRequest.PROCESS_TYPE,
        request_type=ExporterAccessRequest.AGENT_ACCESS,
        status=ExporterAccessRequest.Statuses.CLOSED,
        response=ExporterAccessRequest.REFUSED,
        submitted_by=ilb_admin_user,
        last_updated_by=ilb_admin_user,
        reference="ear/2",
        organisation_name="Export Ltd",
        organisation_address="2 Main Street",
        agent_name="Test Agent",
        agent_address="2 Agent House",
        response_reason="Test refusing request",
    )
    ear.tasks.create(is_active=True, task_type=Task.TaskType.PROCESS)


class IncorrectTypeDFLFirearmsLicenceSerializer(DFLFirearmsLicenceSerializer):
    importer: int
    country_of_origin: int


class IncorrectTypeSupplementaryFirearmsSerializer(SupplementaryFirearmsSerializer):
    importer: int


class IncorrectTypeImportLicenceSerializer(ImportLicenceSerializer):
    importer: int = pydantic.Field(serialization_alias="Importer Name")


class IncorrectTypeImporterAccessRequestReportSerializer(ImporterAccessRequestReportSerializer):
    request_type: int


class IncorrectTypeAccessRequestTotalsReportSerializer(AccessRequestTotalsReportSerializer):
    approved_requests: str


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
        app.submit_datetime = make_aware(dt.datetime(2024, 1, 1, 12, 0, 0))
        app.save()
        for cert in app.certificates.all():
            cert.case_completion_datetime = make_aware(dt.datetime(2024, 1, 9, 13, 7, 0))
            cert.save()

    def test_issued_certificate_report_interface_get_data_header(self):
        interface = IssuedCertificateReportInterface(self.report_schedule)
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_ISSUED_CERTIFICATE_HEADER,
            "results": [],
            "errors": [],
        }

    def test_issued_certificate_report_interface_get_data_cfs_filter_by_legislation(
        self, completed_cfs_app
    ):
        self._setup_app_update_submitted_and_completed_dates(completed_cfs_app)
        self._setup_app_with_case_email(completed_cfs_app, EmailTypes.HSE_CASE_EMAIL, True)
        self.report_schedule.parameters["legislation"] = ["1"]
        self.report_schedule.save()
        interface = IssuedCertificateReportInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == []

    def test_issued_certificate_report_interface_get_data_cfs(self, completed_cfs_app):
        self._setup_app_with_variation_request(completed_cfs_app)
        self._setup_app_update_submitted_and_completed_dates(completed_cfs_app)
        self._setup_app_with_case_email(completed_cfs_app, EmailTypes.HSE_CASE_EMAIL, True)
        self.report_schedule.parameters["legislation"] = ["3"]
        self.report_schedule.save()
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
                "Continent": "Africa",
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
                "Continent": "Middle East, Afghanistan and Pakistan",
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
                "Continent": "China and Hong Kong",
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
                "Continent": "Middle East, Afghanistan and Pakistan",
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
            "errors": [],
        }

    def test_get_errors(self, approved_importer_access_request):
        interface = ImporterAccessRequestInterface(self.report_schedule)
        interface.ReportSerializer = IncorrectTypeImporterAccessRequestReportSerializer
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_IMPORT_ACCESS_REQUEST_HEADER,
            "results": [],
            "errors": [
                {
                    "Error Message": "Input should be a valid integer, unable to parse string as an integer",
                    "Error Type": "Validation Error",
                    "Identifier": "iar/1",
                    "Column": "request_type",
                    "Value": "Importer Access Request",
                    "Report Name": "Importer Access Requests",
                }
            ],
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
            "errors": [],
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
            "errors": [],
        }

    def test_get_errors(self, approved_importer_access_request):
        interface = AccessRequestTotalsInterface(self.report_schedule)
        interface.ReportSerializer = IncorrectTypeAccessRequestTotalsReportSerializer
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_ACCESS_REQUEST_TOTALS_HEADER,
            "results": [],
            "errors": [
                {
                    "Column": "approved_requests",
                    "Error Message": "Input should be a valid string",
                    "Error Type": "Validation Error",
                    "Identifier": "Totals",
                    "Value": 1,
                    "Report Name": "Access Requests Totals",
                }
            ],
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
            "errors": [],
        }

    def test_get_errors(self, completed_dfl_app):
        interface = ImportLicenceInterface(self.report_schedule)
        interface.ReportSerializer = IncorrectTypeImportLicenceSerializer
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_IMPORT_LICENCE_HEADER,
            "results": [],
            "errors": [
                {
                    "Identifier": "IMA/2024/00001",
                    "Error Type": "Validation Error",
                    "Error Message": "Input should be a valid integer, unable to parse string as an integer",
                    "Column": "importer",
                    "Value": "Test Importer 1",
                    "Report Name": "Import Licence Data Extract",
                }
            ],
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


class TestSupplementaryFirearmsInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user, importer_client):
        self.report_schedule = report_schedule
        self.ilb_admin_user = ilb_admin_user
        self.client = importer_client

    def test_get_data_header(self):
        interface = SupplementaryFirearmsInterface(self.report_schedule)
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_SUPPLEMENTARY_FIREARMS_HEADER,
            "results": [],
            "errors": [],
        }

    def test_get_errors(self, completed_dfl_app_with_supplementary_report):
        interface = SupplementaryFirearmsInterface(self.report_schedule)
        interface.ReportSerializer = IncorrectTypeSupplementaryFirearmsSerializer
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_SUPPLEMENTARY_FIREARMS_HEADER,
            "results": [],
            "errors": [
                {
                    "Identifier": "IMA/2024/00001",
                    "Error Type": "Validation Error",
                    "Error Message": "Input should be a valid integer, unable to parse string as an integer",
                    "Column": "importer",
                    "Value": "Test Importer 1",
                    "Report Name": "Supplementary firearms report",
                }
            ],
        }

    def test_get_sil_data(self, completed_sil_app_with_supplementary_report):
        interface = SupplementaryFirearmsInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Licence Reference": "GBSIL0000001B",
                "Case Reference": "IMA/2024/00001",
                "Case Type": "SIL",
                "Importer": "Test Importer 1",
                "Eori Number": "GB1111111111ABCDE",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Afghanistan",
                "Country of Consignment": "Afghanistan",
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria or the Russian Federation."
                "(including any previous name by which these territories have been known).",
                "Constabularies": "Avon & Somerset",
                "Report Date": "13/02/2024",
                "Goods Description": "Section 1 goods",
                "Goods Quantity": 111,
                "Firearms Exceed Quantity": "No",
                "Goods Description with Subsection": "Section 1 goods",
                "Who Bought From Name": "first_name value",
                "Who Bought From Reg No": "registration_number value",
                "Who Bought From Address": "street value, city value, postcode value, region value, Afghanistan",
                "Frame Serial Number": "11111111111",
                "Make/Model": "Test-Section1",
                "Calibre": "1mm",
                "Gun Barrel Proofing meets CIP": "Yes",
                "Firearms Document": "",
                "Date Firearms Received": "13/02/2024",
                "Means of Transport": "air",
                "Reported all firearms for licence": "No",
            },
            {
                "Licence Reference": "GBSIL0000001B",
                "Case Reference": "IMA/2024/00001",
                "Case Type": "SIL",
                "Importer": "Test Importer 1",
                "Eori Number": "GB1111111111ABCDE",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Afghanistan",
                "Country of Consignment": "Afghanistan",
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria or the Russian Federation."
                "(including any previous name by which these territories have been known).",
                "Constabularies": "Avon & Somerset",
                "Report Date": "13/02/2024",
                "Goods Description": "Section 2 goods",
                "Goods Quantity": 222,
                "Firearms Exceed Quantity": "No",
                "Goods Description with Subsection": "Section 2 goods",
                "Who Bought From Name": "first_name value",
                "Who Bought From Reg No": "registration_number value",
                "Who Bought From Address": "street value, city value, postcode value, region value, Afghanistan",
                "Frame Serial Number": "22222222222",
                "Make/Model": "Test-Section2",
                "Calibre": "2mm",
                "Gun Barrel Proofing meets CIP": "No",
                "Firearms Document": "",
                "Date Firearms Received": "13/02/2024",
                "Means of Transport": "air",
                "Reported all firearms for licence": "No",
            },
            {
                "Licence Reference": "GBSIL0000001B",
                "Case Reference": "IMA/2024/00001",
                "Case Type": "SIL",
                "Importer": "Test Importer 1",
                "Eori Number": "GB1111111111ABCDE",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Afghanistan",
                "Country of Consignment": "Afghanistan",
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria or the Russian Federation."
                "(including any previous name by which these territories have been known).",
                "Constabularies": "Avon & Somerset",
                "Report Date": "13/02/2024",
                "Goods Description": "Section 5 goods",
                "Goods Quantity": 333,
                "Firearms Exceed Quantity": "No",
                "Goods Description with Subsection": "Section 5 goods",
                "Who Bought From Name": "first_name value",
                "Who Bought From Reg No": "registration_number value",
                "Who Bought From Address": "street value, city value, postcode value, region value, Afghanistan",
                "Frame Serial Number": "555555555555",
                "Make/Model": "Test-Section5",
                "Calibre": "5mm",
                "Gun Barrel Proofing meets CIP": "No",
                "Firearms Document": "",
                "Date Firearms Received": "13/02/2024",
                "Means of Transport": "air",
                "Reported all firearms for licence": "No",
            },
            {
                "Licence Reference": "GBSIL0000001B",
                "Case Reference": "IMA/2024/00001",
                "Case Type": "SIL",
                "Importer": "Test Importer 1",
                "Eori Number": "GB1111111111ABCDE",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Afghanistan",
                "Country of Consignment": "Afghanistan",
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria or the Russian Federation."
                "(including any previous name by which these territories have been known).",
                "Constabularies": "Avon & Somerset",
                "Report Date": "13/02/2024",
                "Goods Description": "Section 58 obsoletes goods",
                "Goods Quantity": 444,
                "Firearms Exceed Quantity": "No",
                "Goods Description with Subsection": "Section 58 obsoletes goods",
                "Who Bought From Name": "first_name value",
                "Who Bought From Reg No": "registration_number value",
                "Who Bought From Address": "street value, city value, postcode value, region value, Afghanistan",
                "Frame Serial Number": "5555555555551",
                "Make/Model": "Test-Section5-Obsolete",
                "Calibre": "5.1mm",
                "Gun Barrel Proofing meets CIP": "No",
                "Firearms Document": "",
                "Date Firearms Received": "13/02/2024",
                "Means of Transport": "air",
                "Reported all firearms for licence": "No",
            },
            {
                "Licence Reference": "GBSIL0000001B",
                "Case Reference": "IMA/2024/00001",
                "Case Type": "SIL",
                "Importer": "Test Importer 1",
                "Eori Number": "GB1111111111ABCDE",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Afghanistan",
                "Country of Consignment": "Afghanistan",
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria or the Russian Federation."
                "(including any previous name by which these territories have been known).",
                "Constabularies": "Avon & Somerset",
                "Report Date": "13/02/2024",
                "Goods Description": "Section 58 other goods",
                "Goods Quantity": 555,
                "Firearms Exceed Quantity": "No",
                "Goods Description with Subsection": "Section 58 other goods",
                "Who Bought From Name": "first_name value",
                "Who Bought From Reg No": "registration_number value",
                "Who Bought From Address": "street value, city value, postcode value, region value, Afghanistan",
                "Frame Serial Number": "5555555555552",
                "Make/Model": "Test-Section5Others",
                "Calibre": "5.2mm",
                "Gun Barrel Proofing meets CIP": "No",
                "Firearms Document": "",
                "Date Firearms Received": "13/02/2024",
                "Means of Transport": "air",
                "Reported all firearms for licence": "No",
            },
        ]

    def test_get_oil_data(self, completed_oil_app_with_supplementary_report):
        interface = SupplementaryFirearmsInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Licence Reference": "GBOIL0000001B",
                "Case Reference": "IMA/2024/00001",
                "Case Type": "OIL",
                "Importer": "Test Importer 1",
                "Eori Number": "GB1111111111ABCDE",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Any Country",
                "Country of Consignment": "Any Country",
                "Endorsements": (
                    "OPEN INDIVIDUAL LICENCE Not valid for goods originating in "
                    "or consigned from Iran, North Korea, Libya, Syria or the "
                    "Russian Federation.(including any previous name by which "
                    "these territories have been known).\n"
                    "This licence is only valid if the firearm and its essential "
                    "component parts (Barrel, frame, receiver (including both "
                    "upper or lower receiver), slide, cylinder, bolt or breech "
                    "block) are marked with name of manufacturer or brand, "
                    "country or place of manufacturer, serial number, year of "
                    "manufacture and model (if an essential component is too "
                    "small to be fully marked it must at least be marked with a "
                    "serial number or alpha-numeric or digital code)."
                ),
                "Constabularies": "Avon & Somerset",
                "Report Date": "13/02/2024",
                "Goods Description": (
                    "Firearms, component parts thereof, or ammunition of any applicable commodity code, "
                    "other than those falling under Section 5 of the Firearms Act 1968 as amended."
                ),
                "Goods Description with Subsection": (
                    "Firearms, component parts thereof, or ammunition of any applicable commodity code, "
                    "other than those falling under Section 5 of the Firearms Act 1968 as amended."
                ),
                "Goods Quantity": 0,
                "Firearms Exceed Quantity": "No",
                "Who Bought From Name": "first_name value",
                "Who Bought From Reg No": "registration_number value",
                "Who Bought From Address": "street value, city value, postcode value, region value, Afghanistan",
                "Frame Serial Number": "",
                "Make/Model": "",
                "Calibre": "",
                "Gun Barrel Proofing meets CIP": "",
                "Firearms Document": "See uploaded files on report",
                "Date Firearms Received": "13/02/2024",
                "Means of Transport": "air",
                "Reported all firearms for licence": "No",
            },
        ]

    def test_get_dfl_data(self, completed_dfl_app_with_supplementary_report):
        interface = SupplementaryFirearmsInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Licence Reference": "GBSIL0000001B",
                "Case Reference": "IMA/2024/00001",
                "Case Type": "DEACTIVATED",
                "Importer": "Test Importer 1",
                "Eori Number": "GB1111111111ABCDE",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Afghanistan",
                "Country of Consignment": "Albania",
                "Endorsements": "",
                "Constabularies": "Derbyshire",
                "Report Date": "13/02/2024",
                "Goods Description": "goods_description value",
                "Goods Description with Subsection": "goods_description value",
                "Goods Quantity": 1,
                "Firearms Exceed Quantity": "No",
                "Who Bought From Name": "first_name value",
                "Who Bought From Reg No": "registration_number value",
                "Who Bought From Address": "street value, city value, postcode value, region value, Afghanistan",
                "Frame Serial Number": "5555555555552",
                "Make/Model": "DFL Firearm",
                "Calibre": "4.1mm",
                "Gun Barrel Proofing meets CIP": "Yes",
                "Firearms Document": "",
                "Date Firearms Received": "13/02/2024",
                "Means of Transport": "air",
                "Reported all firearms for licence": "No",
            },
        ]


class TestFirearmsLicencesInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user, importer_client):
        self.report_schedule = report_schedule
        self.ilb_admin_user = ilb_admin_user
        self.client = importer_client

    def test_get_data_header(self):
        interface = DFLFirearmsLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_FIREARMS_LICENCES_HEADER,
            "results": [],
            "errors": [],
        }

    def test_get_errors(self, completed_dfl_app):
        interface = DFLFirearmsLicenceInterface(self.report_schedule)
        interface.ReportSerializer = IncorrectTypeDFLFirearmsLicenceSerializer
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_FIREARMS_LICENCES_HEADER,
            "results": [],
            "errors": [
                {
                    "Identifier": "IMA/2024/00001",
                    "Error Type": "Validation Error",
                    "Error Message": "Input should be a valid integer, unable to parse string as an integer",
                    "Column": "importer",
                    "Value": "Test Importer 1",
                    "Report Name": "Deactivated Firearms Licences",
                },
                {
                    "Column": "country_of_origin",
                    "Error Message": "Input should be a valid integer, unable to parse string as an integer",
                    "Error Type": "Validation Error",
                    "Identifier": "IMA/2024/00001",
                    "Report Name": "Deactivated Firearms Licences",
                    "Value": "Afghanistan",
                },
            ],
        }

    def test_get_dfl_data(self, completed_dfl_app):
        interface = DFLFirearmsLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Licence Reference": "GBSIL0000001B",
                "Licence Variation Number": 0,
                "Case Reference": "IMA/2024/00001",
                "Importer": "Test Importer 1",
                "TURN Number": "GB1111111111ABCDE",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "First Submitted Date": "01/01/2024",
                "Final Submitted Date": "01/01/2024",
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Afghanistan",
                "Country of Consignment": "Albania",
                "Goods Description": "goods_description value",
                "Endorsements": "",
                "Revoked": "No",
            }
        ]

    def test_get_oil_data(self, completed_oil_app):
        interface = OILFirearmsLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Licence Reference": "GBOIL0000001B",
                "Licence Variation Number": 0,
                "Case Reference": "IMA/2024/00001",
                "Importer": "Test Importer 1",
                "TURN Number": "GB1111111111ABCDE",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "First Submitted Date": "01/01/2024",
                "Final Submitted Date": "01/01/2024",
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Any Country",
                "Country of Consignment": "Any Country",
                "Endorsements": (
                    "OPEN INDIVIDUAL LICENCE Not valid for goods originating in "
                    "or consigned from Iran, North Korea, Libya, Syria or the "
                    "Russian Federation.(including any previous name by which "
                    "these territories have been known).\n"
                    "This licence is only valid if the firearm and its essential "
                    "component parts (Barrel, frame, receiver (including both "
                    "upper or lower receiver), slide, cylinder, bolt or breech "
                    "block) are marked with name of manufacturer or brand, "
                    "country or place of manufacturer, serial number, year of "
                    "manufacture and model (if an essential component is too "
                    "small to be fully marked it must at least be marked with a "
                    "serial number or alpha-numeric or digital code)."
                ),
                "Revoked": "No",
                "Constabularies": "Avon & Somerset",
                "First Constabulary Email Sent Date": "",
                "Last Constabulary Email Closed Date": "",
            }
        ]

    def test_get_sil_data(self, completed_sil_app, mock_gov_notify_client):
        interface = SILFirearmsLicenceInterface(self.report_schedule)

        with freeze_time("2024-03-09 11:00:00"):
            case_email = create_case_email(
                completed_sil_app,
                EmailTypes.CONSTABULARY_CASE_EMAIL,
                cc=["cc_address@example.com"],  # /PS-IGNORE
            )
            completed_sil_app.case_emails.add(case_email)
            send_case_email(case_email)
            case_email.status = CaseEmail.Status.CLOSED
            case_email.closed_datetime = make_aware(dt.datetime(2024, 3, 10, 9, 0, 0))
            case_email.save()

        data = interface.get_data()
        assert data["results"] == [
            {
                "Licence Reference": "GBSIL0000001B",
                "Licence Variation Number": 0,
                "Case Reference": "IMA/2024/00001",
                "Importer": "Test Importer 1",
                "TURN Number": "GB1111111111ABCDE",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "First Submitted Date": "01/01/2024",
                "Final Submitted Date": "01/01/2024",
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Afghanistan",
                "Country of Consignment": "Afghanistan",
                "Goods Description": (
                    "111 x Section 1 goods to which Section 1 of the Firearms Act 1968, as amended, applies.\n"
                    "222 x Section 2 goods to which Section 2 of the Firearms Act 1968, as amended, applies.\n"
                    "333 x Section 5 goods to which Section 5(A) of the Firearms Act 1968, as amended, applies.\n"
                    "555 x Section 58 other goods to which Section 58(2) of the Firearms Act 1968, as amended, applies.\n"
                    "444 x Section 58 obsoletes goods chambered in the obsolete calibre Obsolete calibre value to which Section 58(2)"
                    " of the Firearms Act 1968, as amended, applies."
                ),
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria or the Russian Federation."
                "(including any previous name by which these territories have been known).",
                "Revoked": "No",
                "Constabularies": "Avon & Somerset",
                "First Constabulary Email Sent Date": "09/03/2024 11:00:00",
                "Last Constabulary Email Closed Date": "10/03/2024 09:00:00",
            }
        ]


class TestActiveUserInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user):
        self.report_schedule = report_schedule
        self.ilb_admin_user = ilb_admin_user

    def test_get_data_header(self):
        interface = ActiveUserInterface(self.report_schedule)
        data = interface.get_data()
        assert data["header"] == EXPECTED_ACTIVE_USER_HEADER
        assert data["errors"] == []

    def test_get_data(self, importer, ilb_admin_two):
        # Makes an admin user an importer to make sure they are excluded from the report
        organisation_add_contact(importer, ilb_admin_two)

        interface = ActiveUserInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Businesses": "",
                "Email Address": "access_request_user@example.com",  # /PS-IGNORE
                "First Name": "access_request_user_first_name",  # /PS-IGNORE
                "Is Exporter": "No",
                "Is Importer": "No",
                "Last Name": "access_request_user_last_name",  # /PS-IGNORE
            },
            {
                "Businesses": "Test Importer 1",
                "Email Address": "I1_main_contact@example.com",  # /PS-IGNORE
                "First Name": "I1_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "No",
                "Is Importer": "Yes",
                "Last Name": "I1_main_contact_last_name",  # /PS-IGNORE
            },
            {
                "Businesses": "Test Importer 1, Test Importer 1 Agent 1",
                "Email Address": "I1_A1_main_contact@example.com",  # /PS-IGNORE
                "First Name": "I1_A1_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "No",
                "Is Importer": "Yes",
                "Last Name": "I1_A1_main_contact_last_name",  # /PS-IGNORE
            },
            {
                "Businesses": "Test Importer 2",
                "Email Address": "I2_main_contact@example.com",  # /PS-IGNORE
                "First Name": "I2_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "No",
                "Is Importer": "Yes",
                "Last Name": "I2_main_contact_last_name",  # /PS-IGNORE
            },
            {
                "Businesses": "Test Exporter 1",
                "Email Address": "E1_main_contact@example.com",  # /PS-IGNORE
                "First Name": "E1_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "Yes",
                "Is Importer": "No",
                "Last Name": "E1_main_contact_last_name",  # /PS-IGNORE
            },
            {
                "Businesses": "Test Exporter 1",
                "Email Address": "E1_secondary_contact@example.com",  # /PS-IGNORE
                "First Name": "E1_secondary_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "Yes",
                "Is Importer": "No",
                "Last Name": "E1_secondary_contact_last_name",  # /PS-IGNORE
            },
            {
                "Businesses": "Test Exporter 1, Test Exporter 1 Agent 1",
                "Email Address": "E1_A1_main_contact@example.com",  # /PS-IGNORE
                "First Name": "E1_A1_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "Yes",
                "Is Importer": "No",
                "Last Name": "E1_A1_main_contact_last_name",  # /PS-IGNORE
            },
            {
                "Businesses": "Test Exporter 2",
                "Email Address": "E2_main_contact@example.com",  # /PS-IGNORE
                "First Name": "E2_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "Yes",
                "Is Importer": "No",
                "Last Name": "E2_main_contact_last_name",  # /PS-IGNORE
            },
        ]
