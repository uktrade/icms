import datetime
from collections import defaultdict
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Iterable, NamedTuple, Optional, Union

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F, Q
from django.db.models.functions import Coalesce
from django.utils.timezone import make_aware

from web.domains.case._import.derogations.models import DerogationsApplication
from web.domains.case._import.fa_dfl.models import DFLApplication
from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
from web.domains.case._import.fa_sil.models import SILApplication
from web.domains.case._import.ironsteel.models import IronSteelApplication
from web.domains.case._import.models import ImportApplication
from web.domains.case._import.opt.models import OutwardProcessingTradeApplication
from web.domains.case._import.sanctions.models import SanctionsAndAdhocApplication
from web.domains.case._import.sps.models import PriorSurveillanceApplication
from web.domains.case._import.textiles.models import TextilesApplication
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.case.export.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    ExportApplication,
)
from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import CaseEmail, UpdateRequest
from web.domains.case.types import ImpOrExpT
from web.flow.models import ProcessTypes
from web.models.shared import YesNoChoices
from web.utils.spreadsheet import XlsxConfig, generate_xlsx_file

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet

    from web.domains.country.models import Country


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
    goods_category: Optional[str] = None
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
class ImportResultRow:
    submitted_at: str
    case_status: CaseStatus
    applicant_details: ApplicantDetails
    commodity_details: CommodityDetails

    # Used to order records
    order_by_datetime: datetime.datetime


@dataclass
class ExportResultRow:
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


def search_applications(terms: SearchTerms, limit: int = 200) -> SearchResults:
    """Main search function used to find applications.

    Returns records matching the supplied search terms.
    """
    app_pks_and_types = _get_search_ids_and_types(terms)

    get_result_row = _get_result_row if terms.case_type == "import" else _get_export_result_row

    records: list[ResultRow] = []

    for queryset in _get_search_records(app_pks_and_types[:limit]):
        for rec in queryset:
            row = get_result_row(rec)  # type:ignore[arg-type]
            records.append(row)  # type:ignore[arg-type]

    # Sort the records by order_by_datetime DESC (submitted date or created date)
    records.sort(key=attrgetter("order_by_datetime"), reverse=True)

    return SearchResults(total_rows=len(app_pks_and_types), records=records)


def get_search_results_spreadsheet(case_type: str, results: SearchResults) -> bytes:
    """Return a spreadsheet of the supplied search results"""

    rows: Iterable[Union[SpreadsheetRow, ExportSpreadsheetRow]]

    if case_type == "import":
        header_data = [
            "Case Reference",
            "Applicant's Reference",
            "Licence Reference",
            "Licence Type",
            "Licence Start Date",
            "Licence End Date",
            "Application Type",
            "Application Sub-Type",
            "Case Status",
            "Chief Usage Status",
            "Submitted Date",
            "Importer",
            "Agent",
            "Application Contact",
            "Country of Origin",
            "Country of Consignment",
            "Shipping Year",
            "Goods Category",
            "Commodity Code(s)",
        ]
        rows = _get_import_spreadsheet_rows(results.records)  # type:ignore[arg-type]

    else:
        header_data = [
            "Case Reference",
            "Certificates",
            "Application Type",
            "Status",
            "Submitted Date",
            "Certificate Countries",
            "Countries of Manufacture",
            "Exporter",
            "Agent",
            "Application Contact",
        ]

        rows = _get_export_spreadsheet_rows(results.records)  # type:ignore[arg-type]

    config = XlsxConfig()
    config.header.data = header_data
    config.header.styles = {"bold": True}
    config.rows = rows  # type: ignore[assignment]
    config.column_width = 25
    config.sheet_name = "Sheet 1"

    return generate_xlsx_file(config)


def get_wildcard_filter(field: str, search_pattern: str) -> dict[str, str]:
    """Return the filter kwargs for the supplied field and search_pattern.

    Strings with `%` are converted into django ORM code using one of several methods.

    :param field: The name of the field to search on
    :param search_pattern: the user supplied search pattern
    """

    if search_pattern.strip() == "%":
        return {}

    # The default search unless changed below
    search_regex = search_pattern.replace("%", ".*")
    search = {f"{field}__iregex": f"^{search_regex}"}
    wildcards = search_pattern.count("%")

    if wildcards == 0:
        search = {f"{field}": search_pattern}

    elif wildcards == 1:
        if search_pattern.startswith("%"):
            search = {f"{field}__iendswith": search_pattern[1:]}

        elif search_pattern.endswith("%"):
            search = {f"{field}__istartswith": search_pattern[:-1]}

    return search


def _get_search_ids_and_types(terms: SearchTerms) -> list[ProcessTypeAndPK]:
    """Search ImportApplication records to find records matching the supplied terms.

    Returns a list of pk and process_type pairs for all matching records.
    """

    model_cls: ImpOrExpT = ImportApplication if terms.case_type == "import" else ExportApplication

    applications = _apply_search(model_cls.objects.all(), terms)
    applications = applications.order_by("-order_by_datetime")
    applications = applications.distinct()

    app_pks_and_types = applications.values_list("pk", "process_type", named=True)

    # evaluate the queryset once
    return list(app_pks_and_types)


def _get_search_records(
    search_ids_and_types: list[ProcessTypeAndPK],
) -> "Iterable[QuerySet[ImportApplication]]":
    """Yields records matching the supplied search_ids and app types."""

    # Create a mapping of process_type -> list of app.pks
    app_pks = defaultdict(list)

    for app in search_ids_and_types:
        app_pks[app.process_type].append(app.pk)

    # Map all available process types to the function used to search those records
    process_type_map = {
        ProcessTypes.DEROGATIONS: _get_derogations_applications,
        ProcessTypes.FA_DFL: _get_fa_dfl_applications,
        ProcessTypes.FA_OIL: _get_fa_oil_applications,
        ProcessTypes.FA_SIL: _get_fa_sil_applications,
        ProcessTypes.IRON_STEEL: _get_ironsteel_applications,
        ProcessTypes.OPT: _get_opt_applications,
        ProcessTypes.SANCTIONS: _get_sanctionadhoc_applications,
        ProcessTypes.SPS: _get_sps_applications,
        ProcessTypes.TEXTILES: _get_textiles_applications,
        ProcessTypes.WOOD: _get_wood_applications,
        ProcessTypes.CFS: _get_cfs_applications,
        ProcessTypes.COM: _get_com_applications,
        ProcessTypes.GMP: _get_gmp_applications,
    }

    for app_pt, search_ids in app_pks.items():  # type:ignore[assignment]
        search_func = process_type_map[app_pt]  # type:ignore[index]

        yield search_func(search_ids)


def _get_result_row(rec: ImportApplication) -> ImportResultRow:
    """Process the incoming application and return a result row."""

    start_date = rec.licence_start_date.strftime("%d %b %Y") if rec.licence_start_date else None
    end_date = rec.licence_end_date.strftime("%d %b %Y") if rec.licence_end_date else None
    licence_validity = " - ".join(filter(None, (start_date, end_date)))

    licence_reference = _get_licence_reference(rec)
    commodity_details = _get_commodity_details(rec)

    if rec.application_type.type == rec.application_type.Types.FIREARMS:
        application_subtype = rec.application_type.get_sub_type_display()
    else:
        application_subtype = ""

    cus = rec.get_chief_usage_status_display() if rec.chief_usage_status else None

    row = ImportResultRow(
        submitted_at=rec.submit_datetime.strftime("%d %b %Y %H:%M:%S"),
        case_status=CaseStatus(
            applicant_reference=getattr(rec, "applicant_reference", ""),
            case_reference=rec.get_reference(),
            licence_reference=licence_reference,
            licence_validity=licence_validity,
            application_type=rec.application_type.get_type_display(),
            application_sub_type=application_subtype,
            status=rec.get_status_display(),
            licence_type="Paper" if rec.issue_paper_licence_only else "Electronic",
            chief_usage_status=cus,
            # TODO: Revisit when implementing ICMSLST-1048
            licence_start_date=None,
            licence_end_date=None,
        ),
        applicant_details=ApplicantDetails(
            organisation_name=rec.importer.name,
            agent_name=rec.agent.name if rec.agent else None,
            application_contact=rec.contact.full_name,
        ),
        commodity_details=commodity_details,
        order_by_datetime=rec.order_by_datetime,  # This is an annotation
    )

    return row


def _get_export_result_row(rec: ExportApplication) -> ExportResultRow:
    app_type_label = ProcessTypes(rec.process_type).label
    application_contact = rec.contact.full_name if rec.contact else ""
    submitted_at = rec.submit_datetime.strftime("%d %b %Y %H:%M:%S") if rec.submit_datetime else ""

    manufacturer_countries = []
    if rec.process_type == ProcessTypes.CFS:
        # This is an annotation and can have a value of [None] for in-progress apps
        manufacturer_countries = [c for c in rec.manufacturer_countries if c]

    # This is an annotation and can have a value of [None] for in-progress apps
    origin_countries = [c for c in rec.origin_countries if c]

    certificates = _get_certificate_references(rec)

    return ExportResultRow(
        case_reference=rec.get_reference(),
        application_type=app_type_label,
        status=rec.get_status_display(),
        certificates=certificates,
        origin_countries=origin_countries,
        organisation_name=rec.exporter.name,
        application_contact=application_contact,
        submitted_at=submitted_at,
        manufacturer_countries=manufacturer_countries,
        agent_name=rec.agent.name if rec.agent else None,
        order_by_datetime=rec.order_by_datetime,  # This is an annotation
    )


def _get_certificate_references(rec: ExportApplication) -> list[str]:
    """Retrieve the certificate references."""

    # TODO: Revisit when implementing ICMSLST-1138
    if rec.process_type == ProcessTypes.CFS:
        certificates = ["CFS/2021/00001", "CFS/2021/00002", "CFS/2021/00003"]
    elif rec.process_type == ProcessTypes.COM:
        certificates = ["COM/2021/00004", "COM/2021/00005", "COM/2021/00006"]
    elif rec.process_type == ProcessTypes.GMP:
        certificates = ["GMP/2021/00007", "GMP/2021/00008", "GMP/2021/00009"]
    else:
        raise NotImplementedError(f"Unknown process type: {rec.process_type}")

    return certificates


def _get_licence_reference(rec: ImportApplication) -> str:
    """Retrieve the licence reference

    Notes when implementing:
        - The Electronic licence has a link to download the licence
    """

    # TODO: Revisit when implementing ICMSLST-1048 (The correct field is rec.licence_reference)
    if rec.issue_paper_licence_only:
        licence_reference = "9001809L (Paper)"
    else:
        licence_reference = "GBSAN9001624X (Electronic)"

    return licence_reference


def _get_commodity_details(rec: ImportApplication) -> CommodityDetails:
    """Load the commodity details section"""

    app_pt = rec.process_type

    if app_pt == ProcessTypes.WOOD:
        wood_app: WoodQuotaApplication = rec

        details = CommodityDetails(
            origin_country="None",  # This is to match legacy for this application type
            shipping_year=wood_app.shipping_year,
            commodity_codes=[wood_app.commodity.commodity_code],
        )

    elif app_pt == ProcessTypes.DEROGATIONS:
        derogation_app: DerogationsApplication = rec

        details = CommodityDetails(
            origin_country=derogation_app.origin_country.name,
            consignment_country=derogation_app.consignment_country.name,
            shipping_year=derogation_app.submit_datetime.year,
            commodity_codes=[derogation_app.commodity.commodity_code],
        )

    elif app_pt == ProcessTypes.FA_DFL:
        fa_dfl_app: DFLApplication = rec

        details = CommodityDetails(
            origin_country=fa_dfl_app.origin_country.name,
            consignment_country=fa_dfl_app.consignment_country.name,
            goods_category=fa_dfl_app.get_commodity_code_display(),
        )

    elif app_pt == ProcessTypes.FA_OIL:
        fa_oil_app: OpenIndividualLicenceApplication = rec

        details = CommodityDetails(
            origin_country=fa_oil_app.origin_country.name,
            consignment_country=fa_oil_app.consignment_country.name,
            goods_category=fa_oil_app.get_commodity_code_display(),
        )

    elif app_pt == ProcessTypes.FA_SIL:
        fa_sil_app: SILApplication = rec

        details = CommodityDetails(
            origin_country=fa_sil_app.origin_country.name,
            consignment_country=fa_sil_app.consignment_country.name,
            goods_category=fa_sil_app.get_commodity_code_display(),
        )

    elif app_pt == ProcessTypes.IRON_STEEL:
        ironsteel_app: IronSteelApplication = rec

        details = CommodityDetails(
            origin_country=ironsteel_app.origin_country.name,
            consignment_country=ironsteel_app.consignment_country.name,
            shipping_year=ironsteel_app.shipping_year,
            goods_category=ironsteel_app.category_commodity_group.group_code,
            commodity_codes=[ironsteel_app.commodity.commodity_code],
        )

    elif app_pt == ProcessTypes.OPT:
        opt_app: OutwardProcessingTradeApplication = rec

        # cp_commodity_codes & teg_commodity_codes are annotations
        commodity_codes = sorted(opt_app.cp_commodity_codes + opt_app.teg_commodity_codes)

        details = CommodityDetails(
            origin_country=opt_app.cp_origin_country.name,
            consignment_country=opt_app.cp_processing_country.name,
            shipping_year=opt_app.submit_datetime.year,
            goods_category=opt_app.cp_category,
            commodity_codes=commodity_codes,
        )

    elif app_pt == ProcessTypes.SANCTIONS:
        sanction_app: SanctionsAndAdhocApplication = rec

        details = CommodityDetails(
            origin_country=sanction_app.origin_country.name,
            consignment_country=sanction_app.consignment_country.name,
            shipping_year=sanction_app.submit_datetime.year,
            commodity_codes=sorted(sanction_app.commodity_codes),
        )

    elif app_pt == ProcessTypes.SPS:
        sps_app: PriorSurveillanceApplication = rec

        details = CommodityDetails(
            origin_country=sps_app.origin_country.name,
            consignment_country=sps_app.consignment_country.name,
            shipping_year=sps_app.submit_datetime.year,
            commodity_codes=[sps_app.commodity.commodity_code],
        )

    elif app_pt == ProcessTypes.TEXTILES:
        textiles_app: TextilesApplication = rec

        details = CommodityDetails(
            origin_country=textiles_app.origin_country.name,
            consignment_country=textiles_app.consignment_country.name,
            goods_category=textiles_app.category_commodity_group.group_code,
            shipping_year=textiles_app.shipping_year,
            commodity_codes=[textiles_app.commodity.commodity_code],
        )

    else:
        raise NotImplementedError(f"Unsupported process type: {app_pt}")

    return details


def _get_derogations_applications(search_ids: list[int]) -> "QuerySet[DerogationsApplication]":
    applications = DerogationsApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related("commodity", "origin_country", "consignment_country")

    return applications


def _get_fa_dfl_applications(search_ids: list[int]) -> "QuerySet[DFLApplication]":
    applications = DFLApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related("origin_country", "consignment_country")

    return applications


def _get_fa_oil_applications(search_ids: list[int]) -> "QuerySet[OpenIndividualLicenceApplication]":
    applications = OpenIndividualLicenceApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related("origin_country", "consignment_country")

    return applications


def _get_fa_sil_applications(search_ids: list[int]) -> "QuerySet[SILApplication]":
    applications = SILApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related("origin_country", "consignment_country")

    return applications


def _get_ironsteel_applications(search_ids: list[int]) -> "QuerySet[IronSteelApplication]":
    applications = IronSteelApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related(
        "origin_country", "consignment_country", "category_commodity_group", "commodity"
    )

    return applications


def _get_opt_applications(search_ids: list[int]) -> "QuerySet[OutwardProcessingTradeApplication]":
    applications = OutwardProcessingTradeApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related("cp_origin_country", "cp_processing_country")

    applications = applications.annotate(
        cp_commodity_codes=ArrayAgg("cp_commodities__commodity_code", distinct=True),
        teg_commodity_codes=ArrayAgg("teg_commodities__commodity_code", distinct=True),
    )

    return applications


def _get_sanctionadhoc_applications(
    search_ids: list[int],
) -> "QuerySet[SanctionsAndAdhocApplication]":
    applications = SanctionsAndAdhocApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related("origin_country", "consignment_country")

    applications = applications.annotate(
        commodity_codes=ArrayAgg(
            "sanctionsandadhocapplicationgoods__commodity__commodity_code", distinct=True
        )
    )

    return applications


def _get_sps_applications(search_ids: list[int]) -> "QuerySet[PriorSurveillanceApplication]":
    applications = PriorSurveillanceApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related("origin_country", "consignment_country", "commodity")

    return applications


def _get_textiles_applications(search_ids: list[int]) -> "QuerySet[TextilesApplication]":
    applications = TextilesApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related(
        "origin_country", "consignment_country", "category_commodity_group", "commodity"
    )

    return applications


def _get_wood_applications(search_ids: list[int]) -> "QuerySet[WoodQuotaApplication]":
    applications = WoodQuotaApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)
    applications = applications.select_related("commodity")

    return applications


def _get_cfs_applications(search_ids: list[int]) -> "QuerySet[CertificateOfFreeSaleApplication]":
    applications = CertificateOfFreeSaleApplication.objects.filter(pk__in=search_ids)
    applications = _apply_export_optimisation(applications)
    applications = applications.annotate(
        manufacturer_countries=ArrayAgg("schedules__country_of_manufacture__name", distinct=True)
    )

    return applications


def _get_com_applications(search_ids: list[int]) -> "QuerySet[CertificateOfManufactureApplication]":
    applications = CertificateOfManufactureApplication.objects.filter(pk__in=search_ids)
    applications = _apply_export_optimisation(applications)

    return applications


def _get_gmp_applications(
    search_ids: list[int],
) -> "QuerySet[CertificateOfGoodManufacturingPracticeApplication]":
    applications = CertificateOfGoodManufacturingPracticeApplication.objects.filter(
        pk__in=search_ids
    )
    applications = _apply_export_optimisation(applications)

    return applications


def _apply_search(model: "QuerySet[Model]", terms: SearchTerms) -> "QuerySet[Model]":
    """Apply all search terms for Import and Export applications."""

    # THe legacy system only includes applications that have been submitted.
    if terms.case_type == "import":
        model = model.exclude(submit_datetime=None)

    if terms.app_type:
        key = "type" if terms.case_type == "import" else "type_code"
        iat_filter = {f"application_type__{key}": terms.app_type}

        if terms.app_sub_type:
            iat_filter["application_type__sub_type"] = terms.app_sub_type

        model = model.filter(**iat_filter)

    if terms.case_ref:
        reference_filter = get_wildcard_filter("reference", terms.case_ref)
        model = model.filter(**reference_filter)

    if terms.licence_ref:
        # TODO: Revisit when implementing ICMSLST-1048
        # Need to wildcard match on the licence_reference field for Import Application's

        # TODO: Revisit when implementing ICMSLST-1138
        # We need to search one or more certificate references (No model field yet)

        raise NotImplementedError("Searching by Licence Reference isn't supported yet")

    if terms.case_status:
        filters = _get_status_to_filter(terms.case_type, terms.case_status)
        model = model.filter(filters)

    if terms.response_decision:
        model = model.filter(decision=terms.response_decision)

    if terms.submitted_date_start:
        start_datetime = make_aware(
            datetime.datetime.combine(terms.submitted_date_start, datetime.datetime.min.time())
        )

        model = model.filter(submit_datetime__gte=start_datetime)

    if terms.submitted_date_end:
        end_datetime = make_aware(
            datetime.datetime.combine(terms.submitted_date_end, datetime.datetime.max.time())
        )

        model = model.filter(submit_datetime__lte=end_datetime)

    if terms.application_contact:
        first_name_filter = get_wildcard_filter("contact__first_name", terms.application_contact)
        last_name_filter = get_wildcard_filter("contact__last_name", terms.application_contact)

        model = model.filter(Q(**first_name_filter) | Q(**last_name_filter))

    if terms.pending_firs == YesNoChoices.yes:
        model = model.filter(further_information_requests__status=FurtherInformationRequest.OPEN)

    if terms.pending_update_reqs == YesNoChoices.yes:
        model = model.filter(update_requests__status=UpdateRequest.Status.OPEN)

    # TODO: Revisit this when doing ICMSLST-964
    # reassignment_search (searches for people not assigned to me)

    if terms.case_type == "import":
        model = _apply_import_application_filter(model, terms)

    if terms.case_type == "export":
        model = _apply_export_application_filter(model, terms)

    model = model.annotate(order_by_datetime=_get_order_by_datetime(terms.case_type))

    return model


def _apply_import_application_filter(
    model: "QuerySet[Model]", terms: SearchTerms
) -> "QuerySet[Model]":

    if terms.applicant_ref:
        applicant_ref_filter = get_wildcard_filter("applicant_reference", terms.applicant_ref)
        model = model.filter(**applicant_ref_filter)

    if terms.importer_agent_name:
        importer_filter = get_wildcard_filter("importer__name", terms.importer_agent_name)
        agent_filter = get_wildcard_filter("agent__name", terms.importer_agent_name)

        model = model.filter(Q(**importer_filter) | Q(**agent_filter))

    if terms.licence_type:
        paper_only = terms.licence_type == "paper"
        model = model.filter(issue_paper_licence_only=paper_only)

    if terms.chief_usage_status:
        model = model.filter(chief_usage_status=terms.chief_usage_status)

    if terms.origin_country:
        country_filter = _get_country_filter(terms.origin_country, "origin_country")
        model = model.filter(**country_filter)

    if terms.consignment_country:
        country_filter = _get_country_filter(terms.consignment_country, "consignment_country")
        model = model.filter(**country_filter)

    if terms.shipping_year:
        # Shipping year only applies to one of the following applications
        ironsteel_query = Q(ironsteelapplication__shipping_year=terms.shipping_year)
        textiles_query = Q(textilesapplication__shipping_year=terms.shipping_year)
        wood_query = Q(woodquotaapplication__shipping_year=terms.shipping_year)

        model = model.filter(ironsteel_query | textiles_query | wood_query)

    # TODO: Write test & implement (This is different for each application that has it)
    if terms.goods_category:
        ...

    # TODO: Write test & implement (This is different for each application that has it)
    if terms.commodity_code:
        ...

    # TODO ICMSLST-686 Write test & implement
    if terms.under_appeal:
        ...

    # In legacy licencing assumes application state is in processing (We won't for now)
    if terms.licence_date_start:
        model = model.filter(licence_start_date__gte=terms.licence_date_start)

    if terms.licence_date_end:
        model = model.filter(licence_end_date__lte=terms.licence_date_end)

    if terms.issue_date_start:
        # TODO: Raise ticket to search by issue date when implemented
        # model = model.filter(issue_date__gte=terms.issue_date_start)
        pass

    if terms.issue_date_end:
        # TODO: Raise ticket to search by issue date when implemented
        # model = model.filter(issue_date__lte=terms.issue_date_end)
        pass

    return model


def _apply_export_application_filter(
    model: "QuerySet[Model]", terms: SearchTerms
) -> "QuerySet[Model]":
    if terms.exporter_agent_name:
        exporter_filter = get_wildcard_filter("exporter__name", terms.exporter_agent_name)
        agent_filter = get_wildcard_filter("agent__name", terms.exporter_agent_name)

        model = model.filter(Q(**exporter_filter) | Q(**agent_filter))

    if terms.closed_date_start:
        # TODO: Implement when doing ICMSLST-1107
        ...

    if terms.closed_date_end:
        # TODO: Implement when doing ICMSLST-1107
        ...

    if terms.certificate_country:
        country_filter = _get_country_filter(terms.certificate_country, "countries")
        model = model.filter(**country_filter)

    if terms.manufacture_country:
        # CFS apps are the only export application with a manufacturing company
        country_filter = _get_country_filter(
            terms.manufacture_country,
            "certificateoffreesaleapplication__schedules__country_of_manufacture",
        )
        model = model.filter(**country_filter)

    return model


def _apply_import_optimisation(model: "QuerySet[Model]") -> "QuerySet[Model]":
    """Selects related tables used for import applications."""
    model = model.select_related("importer", "contact", "application_type")
    model = model.annotate(order_by_datetime=_get_order_by_datetime("import"))

    return model


def _apply_export_optimisation(model: "QuerySet[Model]") -> "QuerySet[Model]":
    """Selects related tables used for import applications."""
    model = model.select_related("exporter", "contact")
    model = model.annotate(
        origin_countries=ArrayAgg("countries__name", distinct=True),
        order_by_datetime=_get_order_by_datetime("export"),
    )

    return model


def _get_order_by_datetime(case_type: str) -> Any:
    if case_type == "import":
        return F("submit_datetime")
    else:
        return Coalesce("submit_datetime", "created")


def _get_country_filter(country_qs: "QuerySet[Country]", field: str) -> dict[str, Any]:
    if country_qs.count() == 1:
        country_filter = {field: country_qs.first()}
    else:
        country_filter = {f"{field}__in": country_qs}

    return country_filter


def _get_import_spreadsheet_rows(records: list[ImportResultRow]) -> Iterable[SpreadsheetRow]:
    """Converts the incoming records in to a spreadsheet row."""

    for row in records:
        cs = row.case_status
        ad = row.applicant_details
        cd = row.commodity_details

        commodity_codes = ", ".join(cd.commodity_codes) if cd.commodity_codes else None

        yield SpreadsheetRow(
            case_reference=cs.case_reference,
            applicant_reference=cs.applicant_reference,
            licence_reference=cs.licence_reference,
            licence_type=cs.licence_type,
            licence_start_date=cs.licence_start_date,
            licence_end_date=cs.licence_end_date,
            application_type=cs.application_type,
            application_sub_type=cs.application_sub_type,
            case_status=cs.status,
            chief_usage_status=cs.chief_usage_status,
            submitted_date=row.submitted_at,
            organisation_name=ad.organisation_name,
            agent=ad.agent_name,
            application_contact=ad.application_contact,
            origin_country=cd.origin_country,
            country_of_consignment=cd.consignment_country,
            shipping_year=cd.shipping_year,
            goods_category=cd.goods_category,
            commodity_codes=commodity_codes,
        )


def _get_export_spreadsheet_rows(records: list[ExportResultRow]) -> Iterable[ExportSpreadsheetRow]:
    for row in records:
        certificates = ", ".join(row.certificates)
        certificate_countries = ", ".join(row.origin_countries)
        manufacturer_countries = ", ".join(row.manufacturer_countries)

        yield ExportSpreadsheetRow(
            case_reference=row.case_reference,
            certificates=certificates,
            application_type=row.application_type,
            case_status=row.status,
            submitted_date=row.submitted_at,
            certificate_countries=certificate_countries,
            manufacturer_countries=manufacturer_countries,
            exporter=row.organisation_name,
            agent=row.agent_name or "",
            application_contact=row.application_contact,
        )


def _get_status_to_filter(case_type: str, case_status: str) -> Q:
    if case_type == "import":
        choices = dict(get_import_status_choices())
    else:
        choices = dict(get_export_status_choices())

    if case_status not in choices:
        raise NotImplementedError(f"Filter ({case_status}) for case status not supported.")

    if case_status == "FIR_REQUESTED":
        filters = Q(further_information_requests__status=FurtherInformationRequest.OPEN)
    elif case_status == "UPDATE_REQUESTED":
        filters = Q(update_requests__status=UpdateRequest.Status.OPEN)
    elif case_status == "BEIS":
        filters = Q(
            certificateofgoodmanufacturingpracticeapplication__case_emails__status=CaseEmail.Status.OPEN
        )
    elif case_status == "HSE":
        filters = Q(certificateoffreesaleapplication__case_emails__status=CaseEmail.Status.OPEN)
    else:
        filters = Q(status=case_status)

    return filters


def get_import_status_choices() -> list[tuple[Any, str]]:
    st = ImportApplication.Statuses

    return [
        (st.COMPLETED.value, st.COMPLETED.label),  # type: ignore[attr-defined]
        (st.PROCESSING.value, st.PROCESSING.label),  # type: ignore[attr-defined]
        ("FIR_REQUESTED", "Processing (FIR)"),
        ("UPDATE_REQUESTED", "Processing (Update)"),
        (st.REVOKED.value, st.REVOKED.label),  # type: ignore[attr-defined]
        (st.STOPPED.value, st.STOPPED.label),  # type: ignore[attr-defined]
        (st.SUBMITTED.value, st.SUBMITTED.label),  # type: ignore[attr-defined]
        (st.VARIATION_REQUESTED.value, st.VARIATION_REQUESTED.label),  # type: ignore[attr-defined]
        (st.WITHDRAWN.value, st.WITHDRAWN.label),  # type: ignore[attr-defined]
    ]


def get_export_status_choices() -> list[tuple[Any, str]]:
    st = ExportApplication.Statuses

    return [
        (st.COMPLETED.value, st.COMPLETED.label),  # type: ignore[attr-defined]
        (st.IN_PROGRESS.value, st.IN_PROGRESS.label),  # type: ignore[attr-defined]
        (st.PROCESSING.value, st.PROCESSING.label),  # type: ignore[attr-defined]
        ("BEIS", "Processing (BEIS)"),
        ("FIR_REQUESTED", "Processing (FIR)"),
        ("HSE", "Processing (HSE)"),
        ("UPDATE_REQUESTED", "Processing (Update)"),
        (st.REVOKED.value, st.REVOKED.label),  # type: ignore[attr-defined]
        (st.STOPPED.value, st.STOPPED.label),  # type: ignore[attr-defined]
        (st.SUBMITTED.value, st.SUBMITTED.label),  # type: ignore[attr-defined]
        (st.VARIATION_REQUESTED.value, st.VARIATION_REQUESTED.label),  # type: ignore[attr-defined]
        (st.WITHDRAWN.value, st.WITHDRAWN.label),  # type: ignore[attr-defined]
    ]
