import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, NamedTuple, Optional, Union

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from web.domains.commodity.models import CommodityGroup
    from web.domains.country.models import Country
    from web.domains.user.models import User


@dataclass
class SearchTerms:
    # import or export - will be used to filter by ImportApplication or ExportApplication
    # Or we will have an ImportSearchTerms / ExportSearchTerms
    case_type: str

    # ---- Common search fields (Import and Export applications) ----
    app_type: Optional[str] = None
    case_status: Optional[str] = None
    case_ref: Optional[str] = None
    licence_ref: Optional[str] = None
    response_decision: Optional[str] = None
    submitted_date_start: Optional[datetime.date] = None
    submitted_date_end: Optional[datetime.date] = None
    reassignment_search: Optional[bool] = False
    reassignment_user: Optional["User"] = None
    application_contact: Optional[str] = None
    pending_firs: Optional[str] = None
    pending_update_reqs: Optional[str] = None

    # ---- Import application fields ----
    # icms_legacy_cases = str = None
    app_sub_type: Optional[str] = None
    applicant_ref: Optional[str] = None
    importer_agent_name: Optional[str] = None
    licence_type: Optional[str] = None
    chief_usage_status: Optional[str] = None
    origin_country: Optional["QuerySet[Country]"] = None
    consignment_country: Optional["QuerySet[Country]"] = None
    shipping_year: Optional[str] = None
    goods_category: Optional["CommodityGroup"] = None
    commodity_code: Optional[str] = None
    under_appeal: Optional[str] = None
    licence_date_start: Optional[datetime.date] = None
    licence_date_end: Optional[datetime.date] = None
    issue_date_start: Optional[datetime.date] = None
    issue_date_end: Optional[datetime.date] = None

    # ---- Export application fields ----
    exporter_agent_name: Optional[str] = None
    closed_date_start: Optional[datetime.date] = None
    closed_date_end: Optional[datetime.date] = None
    certificate_country: Optional["QuerySet[Country]"] = None
    manufacture_country: Optional["QuerySet[Country]"] = None


class ProcessTypeAndPK(NamedTuple):
    process_type: str
    pk: int


@dataclass
class CaseStatus:
    case_reference: str
    application_type: str
    application_sub_type: str
    status: str
    licence_type: str  # Used in spreadsheet
    licence_start_date: Optional[str] = None  # Used in spreadsheet
    licence_end_date: Optional[str] = None  # Used in spreadsheet
    chief_usage_status: Optional[str] = None  # Used in spreadsheet
    applicant_reference: Optional[str] = None
    licence_reference: Optional[str] = None
    licence_validity: Optional[str] = None


@dataclass
class ApplicantDetails:
    organisation_name: str
    application_contact: str
    agent_name: Optional[str] = None


@dataclass
class CommodityDetails:
    origin_country: str
    consignment_country: Optional[str] = None
    goods_category: Optional[str] = None
    shipping_year: Optional[int] = None
    commodity_codes: Optional[list[str]] = None


@dataclass
class AssigneeDetails:
    title: str
    ownership_date: str
    assignee_name: str
    reassignment_date: Optional[str] = None


@dataclass
class SearchAction:
    url: str
    name: str
    icon: str


@dataclass
class ImportResultRow:
    app_pk: int
    actions: list[SearchAction]
    submitted_at: str
    case_status: CaseStatus
    applicant_details: ApplicantDetails
    commodity_details: CommodityDetails
    assignee_details: AssigneeDetails
    # Used to order records
    order_by_datetime: datetime.datetime


@dataclass
class ExportResultRow:
    app_pk: int

    actions: list[SearchAction]

    # Case status fields
    case_reference: str
    application_type: str
    status: str

    # certificates fields
    certificates: list[str]

    submitted_at: str
    # Used to order records
    order_by_datetime: datetime.datetime

    # Certificate details
    origin_countries: list[str]

    # Applicant details
    organisation_name: str
    application_contact: str

    # Certificate details optional
    manufacturer_countries: list[str]

    # Assignee details
    assignee_details: AssigneeDetails

    # Applicant details optional
    agent_name: Optional[str] = None


ResultRow = Union[ImportResultRow, ExportResultRow]


@dataclass
class SearchResults:
    total_rows: int
    records: list[ResultRow]


class SpreadsheetRow(NamedTuple):
    case_reference: str
    applicant_reference: Optional[str]
    licence_reference: Optional[str]
    licence_type: str
    licence_start_date: Optional[str]
    licence_end_date: Optional[str]
    application_type: str
    application_sub_type: str
    case_status: str
    chief_usage_status: Optional[str]
    submitted_date: str
    organisation_name: str
    agent: Optional[str]
    application_contact: str
    origin_country: str
    country_of_consignment: Optional[str]
    shipping_year: Optional[int]
    goods_category: Optional[str]
    commodity_codes: Optional[str]


class ExportSpreadsheetRow(NamedTuple):
    case_reference: str
    certificates: str
    application_type: str
    case_status: str
    submitted_date: str
    certificate_countries: str
    manufacturer_countries: str
    exporter: str
    agent: str
    application_contact: str
