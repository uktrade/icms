import datetime as dt

import pydantic
import pytest
from django.utils.timezone import make_aware
from freezegun import freeze_time

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.mail.constants import CaseEmailCodes
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
from web.reports.constants import UserDateFilterType
from web.reports.interfaces import (
    AccessRequestTotalsInterface,
    ActiveStaffUserInterface,
    ActiveUserInterface,
    DFLFirearmsLicenceInterface,
    ExporterAccessRequestInterface,
    ImporterAccessRequestInterface,
    ImportLicenceInterface,
    IssuedCertificateReportInterface,
    OILFirearmsLicenceInterface,
    RegisteredUserInterface,
    SILFirearmsLicenceInterface,
    SupplementaryFirearmsInterface,
)
from web.reports.serializers import (
    AccessRequestTotalsReportSerializer,
    DFLFirearmsLicenceSerializer,
    ImporterAccessRequestReportSerializer,
    ImportLicenceSerializer,
    SupplementaryFirearmsSerializer,
    UserSerializer,
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
    "Agent",
    "Contact Full Name",
    "Country",
    "Countries of Manufacture",
    "Product Legislation",
    "Responsible Person Statement",
    "Is Manufacturer",
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
    "Final Submission Date",
    "Licence Authorisation Date",
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
    "Primary Email Address",
    "Date Joined",
    "Last Login",
    "Is Importer",
    "Is Exporter",
    "Businesses",
]

EXPECTED_ACTIVE_STAFF_USER_HEADER = [
    "First Name",  # /PS-IGNORE
    "Last Name",  # /PS-IGNORE
    "Email Address",
    "Primary Email Address",
    "Date Joined",
    "Last Login",
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


class IncorrectTypeUserSerializer(UserSerializer):
    date_joined: int


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
        self, app: ImpOrExp, email_type: CaseEmailCodes, completed: bool
    ) -> None:
        case_email = create_case_email(app, email_type)
        if completed:
            send_case_email(case_email, self.ilb_admin_user)
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
        self._setup_app_with_case_email(completed_cfs_app, CaseEmailCodes.HSE_CASE_EMAIL, True)
        self.report_schedule.parameters["legislation"] = ["1"]
        self.report_schedule.save()
        interface = IssuedCertificateReportInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == []

    def test_issued_certificate_report_interface_get_data_cfs(self, completed_cfs_app):
        self._setup_app_with_variation_request(completed_cfs_app)
        self._setup_app_update_submitted_and_completed_dates(completed_cfs_app)
        self._setup_app_with_case_email(completed_cfs_app, CaseEmailCodes.HSE_CASE_EMAIL, True)
        self.report_schedule.parameters["legislation"] = ["241"]
        pl_name = (
            "Regulation (EU) No. 528/2012 of the European Parliament and of the Council concerning the making available on the market and use of"
            " biocidal products, as it has effect in Great Britain"
        )
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
                "Product Legislation": pl_name,
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
                "Product Legislation": pl_name,
                "Responsible Person Statement": "Yes",
                "Submitted Datetime": "01/01/2024 12:00:00",
                "Total Processing Time": "8d 1h 7m",
            },
        ]

    def test_issued_certificate_report_interface_get_data_gmp(self, completed_gmp_app):
        self._setup_app_update_submitted_and_completed_dates(completed_gmp_app)
        self._setup_app_with_case_email(completed_gmp_app, CaseEmailCodes.BEIS_CASE_EMAIL, False)
        self._setup_app_with_case_email(completed_gmp_app, CaseEmailCodes.BEIS_CASE_EMAIL, True)
        self._setup_app_with_case_email(completed_gmp_app, CaseEmailCodes.BEIS_CASE_EMAIL, True)
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

    def test_get_data_sil_and_oil(self, completed_sil_app, completed_oil_app):
        # Both types together to check ordering is correct
        interface = ImportLicenceInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Case Ref": "IMA/2024/00002",
                "Licence Ref": "GBOIL0000002C",
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
            },
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
            },
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
                "Coo Country Name": "Belarus",
                "Coc Country Name": "Afghanistan",
                "Shipping Year": "",
                "Com Group Name": "",
                "Commodity Codes": "Code: 9013109000; Desc: More Commoditites, Code: 4202199090; Desc: Test Goods",
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
        self.today = dt.date.today().strftime("%d/%m/%Y")

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
                "Calibre": "1mm",
                "Case Reference": "IMA/2024/00001",
                "Case Type": "SIL",
                "Constabularies": "Avon & Somerset",
                "Country of Consignment": "Afghanistan",
                "Country of Origin": "Afghanistan",
                "Date Firearms Received": "13/02/2024",
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria, Belarus or the Russian Federation "
                "(including any previous name by which these territories have been known).",
                "Eori Number": "GB1111111111ABCDE",
                "Firearms Document": "",
                "Firearms Exceed Quantity": "No",
                "Frame Serial Number": "11111111111",
                "Goods Description with Subsection": "Section 1 goods",
                "Goods Description": "Section 1 goods",
                "Goods Quantity": 111,
                "Gun Barrel Proofing meets CIP": "Yes",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "Importer": "Test Importer 1",
                "Licence Expiry Date": "31/12/2024",
                "Licence Reference": "GBSIL0000001B",
                "Licence Start Date": "01/06/2020",
                "Make/Model": "Test-Section1",
                "Means of Transport": "air",
                "Report Date": self.today,
                "Reported all firearms for licence": "No",
                "Who Bought From Address": "street value, city value, postcode value, region value, Afghanistan",
                "Who Bought From Name": "first_name value",
                "Who Bought From Reg No": "registration_number value",
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
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria, Belarus or the Russian Federation "
                "(including any previous name by which these territories have been known).",
                "Constabularies": "Avon & Somerset",
                "Report Date": self.today,
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
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria, Belarus or the Russian Federation "
                "(including any previous name by which these territories have been known).",
                "Constabularies": "Avon & Somerset",
                "Report Date": self.today,
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
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria, Belarus or the Russian Federation "
                "(including any previous name by which these territories have been known).",
                "Constabularies": "Avon & Somerset",
                "Report Date": self.today,
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
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria, Belarus or the Russian Federation "
                "(including any previous name by which these territories have been known).",
                "Constabularies": "Avon & Somerset",
                "Report Date": self.today,
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
                "Calibre": "",
                "Case Reference": "IMA/2024/00001",
                "Case Type": "OIL",
                "Constabularies": "Avon & Somerset",
                "Country of Consignment": "Any Country",
                "Country of Origin": "Any Country",
                "Date Firearms Received": "13/02/2024",
                "Endorsements": (
                    "OPEN INDIVIDUAL LICENCE Not valid for goods originating in "
                    "or consigned from Iran, North Korea, Libya, Syria, Belarus "
                    "or the Russian Federation (including any previous name by "
                    "which these territories have been known). \n\n"
                    "This licence is only valid if the firearm and its essential "
                    "component parts (Barrel, frame, receiver (including both "
                    "upper or lower receiver), slide, cylinder, bolt or breech "
                    "block) are marked with name of manufacturer or brand, "
                    "country or place of manufacturer, serial number and the  "
                    "year of manufacture (if not part of the serial number) and "
                    "model (where feasible). If an essential component is too "
                    "small to be fully marked it must at least be marked with a "
                    "serial number or alpha-numeric or digital code. If the item "
                    "is not marked as set out above you have 1 month from entry "
                    "into the UK to comply with this requirement. If the item is "
                    "being imported for deactivation, you have three months to "
                    "either comply or have the item deactivated.\n"
                    "Items must be marked using the Latin alphabet and the "
                    "Arabic numeral system. The font size must be at least 1,6 "
                    "mm unless the relevant component parts are too small to be "
                    "marked to this size, in which case a smaller font size may "
                    "be used. \n"
                    "For frames or receivers made from a non-metallic material, "
                    "the marking should be applied to a metal plate that is "
                    "permanently embedded in the material of the frame or "
                    "receiver in such a way that the plate cannot be easily or "
                    "readily removed; and removing the plate would destroy a "
                    "portion of the frame or receiver.  Other techniques for "
                    "marking such frames or receivers are permitted, provided "
                    "those techniques ensure an equivalent level of clarity and "
                    "permanence for the marking."
                ),
                "Eori Number": "GB1111111111ABCDE",
                "Firearms Document": "See uploaded files on report",
                "Firearms Exceed Quantity": "No",
                "Frame Serial Number": "",
                "Goods Description": (
                    "Firearms, component parts thereof, or ammunition of any applicable commodity code, "
                    "other than those falling under Section 5 of the Firearms Act 1968 as amended."
                ),
                "Goods Description with Subsection": (
                    "Firearms, component parts thereof, or ammunition of any applicable commodity code, "
                    "other than those falling under Section 5 of the Firearms Act 1968 as amended."
                ),
                "Goods Quantity": 0,
                "Gun Barrel Proofing meets CIP": "",
                "Importer Address": "I1 address line 1, I1 address line 2, BT180LZ",  # /PS-IGNORE
                "Importer": "Test Importer 1",
                "Licence Expiry Date": "31/12/2024",
                "Licence Reference": "GBOIL0000001B",
                "Licence Start Date": "01/06/2020",
                "Make/Model": "",
                "Means of Transport": "air",
                "Report Date": self.today,
                "Reported all firearms for licence": "No",
                "Who Bought From Address": "street value, city value, postcode value, region value, Afghanistan",
                "Who Bought From Name": "first_name value",
                "Who Bought From Reg No": "registration_number value",
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
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria, Belarus or the Russian Federation "
                "(including any previous name by which these territories have been known).",
                "Constabularies": "Derbyshire",
                "Report Date": self.today,
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
                "Final Submission Date": "01/01/2024",
                "Licence Authorisation Date": "01/06/2020",
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Afghanistan",
                "Country of Consignment": "Albania",
                "Goods Description": "goods_description value",
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria, Belarus or the Russian Federation "
                "(including any previous name by which these territories have been known).",
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
                "Final Submission Date": "01/01/2024",
                "Licence Authorisation Date": "01/06/2020",
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Any Country",
                "Country of Consignment": "Any Country",
                "Endorsements": (
                    "OPEN INDIVIDUAL LICENCE Not valid for goods originating in "
                    "or consigned from Iran, North Korea, Libya, Syria, Belarus "
                    "or the Russian Federation (including any previous name by "
                    "which these territories have been known). \n\n"
                    "This licence is only valid if the firearm and its essential "
                    "component parts (Barrel, frame, receiver (including both "
                    "upper or lower receiver), slide, cylinder, bolt or breech "
                    "block) are marked with name of manufacturer or brand, "
                    "country or place of manufacturer, serial number and the  "
                    "year of manufacture (if not part of the serial number) and "
                    "model (where feasible). If an essential component is too "
                    "small to be fully marked it must at least be marked with a "
                    "serial number or alpha-numeric or digital code. If the item "
                    "is not marked as set out above you have 1 month from entry "
                    "into the UK to comply with this requirement. If the item is "
                    "being imported for deactivation, you have three months to "
                    "either comply or have the item deactivated.\n"
                    "Items must be marked using the Latin alphabet and the "
                    "Arabic numeral system. The font size must be at least 1,6 "
                    "mm unless the relevant component parts are too small to be "
                    "marked to this size, in which case a smaller font size may "
                    "be used. \n"
                    "For frames or receivers made from a non-metallic material, "
                    "the marking should be applied to a metal plate that is "
                    "permanently embedded in the material of the frame or "
                    "receiver in such a way that the plate cannot be easily or "
                    "readily removed; and removing the plate would destroy a "
                    "portion of the frame or receiver.  Other techniques for "
                    "marking such frames or receivers are permitted, provided "
                    "those techniques ensure an equivalent level of clarity and "
                    "permanence for the marking."
                ),
                "Revoked": "No",
                "Constabularies": "Avon & Somerset",
                "First Constabulary Email Sent Date": "",
                "Last Constabulary Email Closed Date": "",
            }
        ]

    def test_get_sil_data(self, completed_sil_app, mock_gov_notify_client):
        interface = SILFirearmsLicenceInterface(self.report_schedule)

        # Use BST datetime to test offset in output
        with freeze_time("2024-07-09 11:00:00"):
            case_email = create_case_email(
                completed_sil_app,
                CaseEmailCodes.CONSTABULARY_CASE_EMAIL,
                cc=["cc_address@example.com"],  # /PS-IGNORE
            )
            completed_sil_app.case_emails.add(case_email)
            send_case_email(case_email, self.ilb_admin_user)
            case_email.status = CaseEmail.Status.CLOSED
            case_email.closed_datetime = dt.datetime(2024, 7, 10, 9, 0, 0, tzinfo=dt.UTC)
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
                "Final Submission Date": "01/01/2024",
                "Licence Authorisation Date": "01/06/2020",
                "Licence Start Date": "01/06/2020",
                "Licence Expiry Date": "31/12/2024",
                "Country of Origin": "Afghanistan",
                "Country of Consignment": "Afghanistan",
                "Goods Description": (
                    "111 x Section 1 goods to which Section 1 of the Firearms Act 1968, as amended, applies.\n"
                    "222 x Section 2 goods to which Section 2 of the Firearms Act 1968, as amended, applies.\n"
                    "333 x Section 5 goods to which Section 5(A) of the Firearms Act 1968, as amended, applies.\n"
                    "Unlimited x Unlimited Section 5 goods to which Section 5(A) of the Firearms Act 1968, as amended, applies.\n"
                    "555 x Section 58 other goods to which Section 58(2) of the Firearms Act 1968, as amended, applies.\n"
                    "444 x Section 58 obsoletes goods chambered in the obsolete calibre .22 Extra Long Maynard to which Section 58(2)"
                    " of the Firearms Act 1968, as amended, applies."
                ),
                "Endorsements": "Not valid for items originating in or consigned from Iran, North Korea, Libya, Syria, Belarus or the Russian Federation "
                "(including any previous name by which these territories have been known).",
                "Revoked": "No",
                "Constabularies": "Avon & Somerset",
                # Should be one hour ahead of freeze_time above.
                "First Constabulary Email Sent Date": "09/07/2024 12:00:00",
                "Last Constabulary Email Closed Date": "10/07/2024 10:00:00",
            }
        ]


class TestActiveUserInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user):
        self.report_schedule = report_schedule
        self.report_schedule.parameters["date_filter_type"] = UserDateFilterType.DATE_JOINED
        self.ilb_admin_user = ilb_admin_user

    def test_get_data_header(self):
        interface = ActiveUserInterface(self.report_schedule)
        data = interface.get_data()
        assert data["header"] == EXPECTED_ACTIVE_USER_HEADER
        assert data["errors"] == []

    @freeze_time("2024-02-11 12:00:00")
    def test_get_data(self, importer, ilb_admin_two, importer_client, importer_one_contact):
        importer_client.force_login(importer_one_contact)
        # Makes an admin user an importer to make sure they are excluded from the report
        organisation_add_contact(importer, ilb_admin_two)

        user_email = importer_one_contact.emails.get(is_primary=True)
        user_email.email = "I1_main_contact_alt_email@example.com"  # /PS-IGNORE
        user_email.save()

        interface = ActiveUserInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Businesses": "Test Importer 1",
                "Email Address": "I1_main_contact@example.com",  # /PS-IGNORE
                "Primary Email Address": "I1_main_contact_alt_email@example.com",  # /PS-IGNORE
                "First Name": "I1_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "No",
                "Is Importer": "Yes",
                "Last Name": "I1_main_contact_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "11/02/2024",
            },
            {
                "Businesses": "Test Importer 1, Test Importer 1 Agent 1",
                "Email Address": "I1_A1_main_contact@example.com",  # /PS-IGNORE
                "Primary Email Address": "I1_A1_main_contact@example.com",  # /PS-IGNORE
                "First Name": "I1_A1_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "No",
                "Is Importer": "Yes",
                "Last Name": "I1_A1_main_contact_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Businesses": "Test Importer 2",
                "Email Address": "I2_main_contact@example.com",  # /PS-IGNORE
                "Primary Email Address": "I2_main_contact@example.com",  # /PS-IGNORE
                "First Name": "I2_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "No",
                "Is Importer": "Yes",
                "Last Name": "I2_main_contact_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Businesses": "Test Exporter 1",
                "Email Address": "E1_main_contact@example.com",  # /PS-IGNORE
                "Primary Email Address": "E1_main_contact@example.com",  # /PS-IGNORE
                "First Name": "E1_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "Yes",
                "Is Importer": "No",
                "Last Name": "E1_main_contact_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Businesses": "Test Exporter 1",
                "Email Address": "E1_secondary_contact@example.com",  # /PS-IGNORE
                "Primary Email Address": "E1_secondary_contact@example.com",  # /PS-IGNORE
                "First Name": "E1_secondary_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "Yes",
                "Is Importer": "No",
                "Last Name": "E1_secondary_contact_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Businesses": "Test Exporter 1, Test Exporter 1 Agent 1",
                "Email Address": "E1_A1_main_contact@example.com",  # /PS-IGNORE
                "Primary Email Address": "E1_A1_main_contact@example.com",  # /PS-IGNORE
                "First Name": "E1_A1_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "Yes",
                "Is Importer": "No",
                "Last Name": "E1_A1_main_contact_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Businesses": "Test Exporter 2",
                "Email Address": "E2_main_contact@example.com",  # /PS-IGNORE
                "Primary Email Address": "E2_main_contact@example.com",  # /PS-IGNORE
                "First Name": "E2_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "Yes",
                "Is Importer": "No",
                "Last Name": "E2_main_contact_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
        ]

    @freeze_time("2024-02-11 12:00:00")
    def test_get_data_filtered_by_last_login(
        self, importer, ilb_admin_two, importer_client, importer_one_contact
    ):
        importer_client.force_login(importer_one_contact)
        self.report_schedule.parameters["date_filter_type"] = UserDateFilterType.LAST_LOGIN
        interface = ActiveUserInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Businesses": "Test Importer 1",
                "Email Address": "I1_main_contact@example.com",  # /PS-IGNORE
                "Primary Email Address": "I1_main_contact@example.com",  # /PS-IGNORE
                "First Name": "I1_main_contact_first_name",  # /PS-IGNORE
                "Is Exporter": "No",
                "Is Importer": "Yes",
                "Last Name": "I1_main_contact_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "11/02/2024",
            }
        ]


class TestActiveStaffUserInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user):
        self.report_schedule = report_schedule
        self.report_schedule.parameters["date_filter_type"] = UserDateFilterType.DATE_JOINED
        self.ilb_admin_user = ilb_admin_user

    def test_get_data_header(self):
        interface = ActiveStaffUserInterface(self.report_schedule)
        data = interface.get_data()
        assert data["header"] == EXPECTED_ACTIVE_STAFF_USER_HEADER
        assert data["errors"] == []

    def test_get_data(self, ilb_admin_two):
        user_email = ilb_admin_two.emails.get(is_primary=True)
        user_email.email = "ilb_admin_two_alt_email@example.com"  # /PS-IGNORE
        user_email.save()

        interface = ActiveStaffUserInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Email Address": "ilb_admin_user@example.com",  # /PS-IGNORE
                "Primary Email Address": "ilb_admin_user@example.com",  # /PS-IGNORE
                "First Name": "ilb_admin_user_first_name",  # /PS-IGNORE
                "Last Name": "ilb_admin_user_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Email Address": "ilb_admin_two@example.com",  # /PS-IGNORE
                "Primary Email Address": "ilb_admin_two_alt_email@example.com",  # /PS-IGNORE
                "First Name": "ilb_admin_two_first_name",  # /PS-IGNORE
                "Last Name": "ilb_admin_two_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Email Address": "nca_admin_user@example.com",  # /PS-IGNORE
                "Primary Email Address": "nca_admin_user@example.com",  # /PS-IGNORE
                "First Name": "nca_admin_user_first_name",  # /PS-IGNORE
                "Last Name": "nca_admin_user_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Email Address": "ho_admin_user@example.com",  # /PS-IGNORE
                "Primary Email Address": "ho_admin_user@example.com",  # /PS-IGNORE
                "First Name": "ho_admin_user_first_name",  # /PS-IGNORE
                "Last Name": "ho_admin_user_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Email Address": "san_admin_user@example.com",  # /PS-IGNORE
                "Primary Email Address": "san_admin_user@example.com",  # /PS-IGNORE
                "First Name": "san_admin_user_first_name",  # /PS-IGNORE
                "Last Name": "san_admin_user_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Email Address": "import_search_user@example.com",  # /PS-IGNORE
                "Primary Email Address": "import_search_user@example.com",  # /PS-IGNORE
                "First Name": "import_search_user_first_name",  # /PS-IGNORE
                "Last Name": "import_search_user_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
            {
                "Email Address": "con_user@example.com",  # /PS-IGNORE
                "Primary Email Address": "con_user@example.com",  # /PS-IGNORE
                "First Name": "con_user_first_name",  # /PS-IGNORE
                "Last Name": "con_user_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            },
        ]


class TestRegisteredUserInterface:
    @pytest.fixture(autouse=True)
    def _setup(self, report_schedule, ilb_admin_user):
        self.report_schedule = report_schedule
        self.report_schedule.parameters["date_filter_type"] = UserDateFilterType.DATE_JOINED
        self.ilb_admin_user = ilb_admin_user

    def test_get_data_header(self):
        interface = RegisteredUserInterface(self.report_schedule)
        data = interface.get_data()
        assert data["header"] == EXPECTED_ACTIVE_USER_HEADER
        assert data["errors"] == []

    def test_get_errors(self):
        interface = RegisteredUserInterface(self.report_schedule)
        interface.ReportSerializer = IncorrectTypeUserSerializer
        data = interface.get_data()
        assert data == {
            "header": EXPECTED_ACTIVE_USER_HEADER,
            "results": [],
            "errors": [
                {
                    "Identifier": "access_request_user@example.com",  # /PS-IGNORE
                    "Error Type": "Validation Error",
                    "Error Message": "Input should be a valid integer",
                    "Column": "date_joined",
                    "Value": "2024-01-20",
                    "Report Name": "Registered Users",
                }
            ],
        }

    def test_get_data(self, importer, ilb_admin_two, access_request_user):
        # Makes an admin user an importer to make sure they are excluded from the report
        organisation_add_contact(importer, ilb_admin_two)
        user_email = access_request_user.emails.get(is_primary=True)
        user_email.email = "access_request_user_alt_email@example.com"  # /PS-IGNORE
        user_email.save()

        interface = RegisteredUserInterface(self.report_schedule)
        data = interface.get_data()
        assert data["results"] == [
            {
                "Businesses": "",
                "Email Address": "access_request_user@example.com",  # /PS-IGNORE
                "Primary Email Address": "access_request_user_alt_email@example.com",  # /PS-IGNORE
                "First Name": "access_request_user_first_name",  # /PS-IGNORE
                "Is Exporter": "No",
                "Is Importer": "No",
                "Last Name": "access_request_user_last_name",  # /PS-IGNORE
                "Date Joined": "20/01/2024",
                "Last Login": "",
            }
        ]
