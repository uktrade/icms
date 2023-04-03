import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, NamedTuple, Optional, Union

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from web.models import CommodityGroup, Country, User


@dataclass
class SearchTerms:
    # import or export - will be used to filter by ImportApplication or ExportApplication
    # Or we will have an ImportSearchTerms / ExportSearchTerms
    case_type: Literal["import", "export"]

    # ---- Common search fields (Import and Export applications) ----
    app_type: str | None = None
    case_status: str | None = None
    case_ref: str | None = None
    licence_ref: str | None = None
    response_decision: str | None = None
    submitted_date_start: datetime.date | None = None
    submitted_date_end: datetime.date | None = None
    reassignment_search: bool | None = False
    reassignment_user: Optional["User"] = None
    application_contact: str | None = None
    pending_firs: str | None = None
    pending_update_reqs: str | None = None

    # ---- Import application fields ----
    # icms_legacy_cases = str = None
    app_sub_type: str | None = None
    applicant_ref: str | None = None
    importer_agent_name: str | None = None
    licence_type: str | None = None
    chief_usage_status: str | None = None
    origin_country: Optional["QuerySet[Country]"] = None
    consignment_country: Optional["QuerySet[Country]"] = None
    shipping_year: str | None = None
    goods_category: Optional["CommodityGroup"] = None
    commodity_code: str | None = None
    under_appeal: str | None = None
    licence_date_start: datetime.date | None = None
    licence_date_end: datetime.date | None = None
    issue_date_start: datetime.date | None = None
    issue_date_end: datetime.date | None = None

    # ---- Export application fields ----
    exporter_agent_name: str | None = None
    closed_date_start: datetime.date | None = None
    closed_date_end: datetime.date | None = None
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
    licence_start_date: str | None = None  # Used in spreadsheet
    licence_end_date: str | None = None  # Used in spreadsheet
    chief_usage_status: str | None = None  # Used in spreadsheet
    applicant_reference: str | None = None
    licence_reference: str | None = None
    licence_reference_link: str | None = None
    licence_validity: str | None = None


@dataclass
class ApplicantDetails:
    organisation_name: str
    application_contact: str
    agent_name: str | None = None


@dataclass
class CommodityDetails:
    origin_country: str
    consignment_country: str | None = None
    goods_category: str | None = None
    shipping_year: int | None = None
    commodity_codes: list[str] | None = None


@dataclass
class AssigneeDetails:
    title: str
    ownership_date: str
    assignee_name: str
    reassignment_date: str | None = None


@dataclass
class SearchAction:
    url: str
    name: str
    label: str
    icon: str
    is_post: bool = True


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

    certificates: list[tuple[str, str]]

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
    agent_name: str | None = None


ResultRow = Union[ImportResultRow, ExportResultRow]


@dataclass
class SearchResults:
    total_rows: int
    records: list[ResultRow]


class SpreadsheetRow(NamedTuple):
    case_reference: str
    applicant_reference: str | None
    licence_reference: str | None
    licence_type: str
    licence_start_date: str | None
    licence_end_date: str | None
    application_type: str
    application_sub_type: str
    case_status: str
    chief_usage_status: str | None
    submitted_date: str
    organisation_name: str
    agent: str | None
    application_contact: str
    origin_country: str
    country_of_consignment: str | None
    shipping_year: int | None
    goods_category: str | None
    commodity_codes: str | None


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
