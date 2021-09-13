import datetime
from collections import defaultdict
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING, Iterable, NamedTuple, Optional

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.utils.timezone import make_aware

from web.domains.case._import.derogations.models import DerogationsApplication
from web.domains.case._import.fa_dfl.models import DFLApplication
from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
from web.domains.case._import.fa_sil.models import SILApplication
from web.domains.case._import.ironsteel.models import IronSteelApplication
from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.case._import.opt.models import OutwardProcessingTradeApplication
from web.domains.case._import.sanctions.models import SanctionsAndAdhocApplication
from web.domains.case._import.sps.models import PriorSurveillanceApplication
from web.domains.case._import.textiles.models import TextilesApplication
from web.domains.case._import.wood.models import WoodQuotaApplication
from web.utils.spreadsheet import XlsxConfig, generate_xlsx_file

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet


@dataclass
class SearchTerms:
    # import or export - will be used to filter by ImportApplication or ExportApplication
    # Or we will have an ImportSearchTerms / ExportSearchTerms
    case_type: str

    # Search fields
    case_ref: Optional[str] = None
    licence_ref: Optional[str] = None
    # icms_legacy_cases = str = None
    app_type: Optional[str] = None
    app_sub_type: Optional[str] = None
    case_status: Optional[str] = None
    response_decision: Optional[str] = None
    importer_agent_name: Optional[str] = None
    submitted_date_start: Optional[datetime.date] = None
    submitted_date_end: Optional[datetime.date] = None
    licence_date_start: Optional[datetime.date] = None
    licence_date_end: Optional[datetime.date] = None
    issue_date_start: Optional[datetime.date] = None
    issue_date_end: Optional[datetime.date] = None
    reassignment_search: Optional[bool] = False


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
    submit_datetime: datetime.datetime


@dataclass
class SearchResults:
    total_rows: int
    records: list[ImportResultRow]


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


def search_applications(terms: SearchTerms, limit: int = 200) -> SearchResults:
    """Main search function used to find applications.

    Returns records matching the supplied search terms.
    """
    app_pks_and_types = _get_search_ids_and_types(terms)

    records = []
    for queryset in _get_search_records(app_pks_and_types[:limit]):
        for rec in queryset:
            row = _get_result_row(rec)
            records.append(row)

    # Sort the records by submit_datetime DESC
    records.sort(key=attrgetter("submit_datetime"), reverse=True)

    return SearchResults(total_rows=len(app_pks_and_types), records=records)


def get_search_results_spreadsheet(results: SearchResults) -> bytes:
    """Return a spreadsheet of the supplied search results"""

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

    config = XlsxConfig()
    config.header.data = header_data
    config.header.styles = {"bold": True}
    config.rows = _get_spreadsheet_rows(results.records)  # type:ignore[assignment]
    config.column_width = 25
    config.sheet_name = "Sheet 1"

    return generate_xlsx_file(config)


def _get_search_ids_and_types(terms: SearchTerms) -> list[ProcessTypeAndPK]:
    """Search ImportApplication records to find records matching the supplied terms.

    Returns a list of pk and process_type pairs for all matching records.
    """

    import_applications = _apply_search(ImportApplication.objects.all(), terms)
    import_applications = import_applications.order_by("-submit_datetime")
    app_pks_and_types = import_applications.values_list("pk", "process_type", named=True)

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
    pt = ImportApplicationType.ProcessTypes

    process_type_map = {
        pt.DEROGATIONS: _get_derogations_applications,
        pt.FA_DFL: _get_fa_dfl_applications,
        pt.FA_OIL: _get_fa_oil_applications,
        pt.FA_SIL: _get_fa_sil_applications,
        pt.IRON_STEEL: _get_ironsteel_applications,
        pt.OPT: _get_opt_applications,
        pt.SANCTIONS: _get_sanctionadhoc_applications,
        pt.SPS: _get_sps_applications,
        pt.TEXTILES: _get_textiles_applications,
        pt.WOOD: _get_wood_applications,
    }

    for pt, search_ids in app_pks.items():  # type:ignore[assignment]
        search_func = process_type_map[pt]  # type:ignore[index]

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
        submit_datetime=rec.submit_datetime,
    )

    return row


def _get_licence_reference(rec: ImportApplication) -> str:
    """Retrieve the licence reference

    Notes when implementing:
        - The Electronic licence has a link to download the licence
    """

    # TODO: Revisit when implementing ICMSLST-1048
    if rec.issue_paper_licence_only:
        licence_reference = "9001809L (Paper)"
    else:
        licence_reference = "GBSAN9001624X (Electronic)"

    return licence_reference


def _get_commodity_details(rec: ImportApplication) -> CommodityDetails:
    """Load the commodity details section"""

    app_pt = rec.process_type
    process_types = ImportApplicationType.ProcessTypes

    if app_pt == process_types.WOOD:
        wood_app: WoodQuotaApplication = rec

        details = CommodityDetails(
            origin_country="None",  # This is to match legacy for this application type
            shipping_year=wood_app.shipping_year,
            commodity_codes=[wood_app.commodity.commodity_code],
        )

    elif app_pt == process_types.DEROGATIONS:
        derogation_app: DerogationsApplication = rec

        details = CommodityDetails(
            origin_country=derogation_app.origin_country.name,
            consignment_country=derogation_app.consignment_country.name,
            shipping_year=derogation_app.submit_datetime.year,
            commodity_codes=[derogation_app.commodity.commodity_code],
        )

    elif app_pt == process_types.FA_DFL:
        fa_dfl_app: DFLApplication = rec

        details = CommodityDetails(
            origin_country=fa_dfl_app.origin_country.name,
            consignment_country=fa_dfl_app.consignment_country.name,
            goods_category=fa_dfl_app.get_commodity_code_display(),
        )

    elif app_pt == process_types.FA_OIL:
        fa_oil_app: OpenIndividualLicenceApplication = rec

        details = CommodityDetails(
            origin_country=fa_oil_app.origin_country.name,
            consignment_country=fa_oil_app.consignment_country.name,
            goods_category=fa_oil_app.get_commodity_code_display(),
        )

    elif app_pt == process_types.FA_SIL:
        fa_sil_app: SILApplication = rec

        details = CommodityDetails(
            origin_country=fa_sil_app.origin_country.name,
            consignment_country=fa_sil_app.consignment_country.name,
            goods_category=fa_sil_app.get_commodity_code_display(),
        )

    elif app_pt == process_types.IRON_STEEL:
        ironsteel_app: IronSteelApplication = rec

        details = CommodityDetails(
            origin_country=ironsteel_app.origin_country.name,
            consignment_country=ironsteel_app.consignment_country.name,
            shipping_year=ironsteel_app.shipping_year,
            goods_category=ironsteel_app.category_commodity_group.group_code,
            commodity_codes=[ironsteel_app.commodity.commodity_code],
        )

    elif app_pt == process_types.OPT:
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

    elif app_pt == process_types.SANCTIONS:
        sanction_app: SanctionsAndAdhocApplication = rec

        details = CommodityDetails(
            origin_country=sanction_app.origin_country.name,
            consignment_country=sanction_app.consignment_country.name,
            shipping_year=sanction_app.submit_datetime.year,
            commodity_codes=sorted(sanction_app.commodity_codes),
        )

    elif app_pt == process_types.SPS:
        sps_app: PriorSurveillanceApplication = rec

        details = CommodityDetails(
            origin_country=sps_app.origin_country.name,
            consignment_country=sps_app.consignment_country.name,
            shipping_year=sps_app.submit_datetime.year,
            commodity_codes=[sps_app.commodity.commodity_code],
        )

    elif app_pt == process_types.TEXTILES:
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


def _apply_search(model: "QuerySet[Model]", terms: SearchTerms) -> "QuerySet[Model]":
    """Apply common filtering to the supplied model - Currently just ImportApplications."""

    # THe legacy system only includes applications that have been submitted.
    model = model.exclude(submit_datetime=None)

    if terms.app_type:
        iat_filter = {"application_type__type": terms.app_type}

        if terms.app_sub_type:
            iat_filter["application_type__sub_type"] = terms.app_sub_type

        model = model.filter(**iat_filter)

    if terms.case_ref:
        # TODO: Revisit this when doing ICMSLST-1035
        model = model.filter(reference=terms.case_ref)

    if terms.licence_ref:
        raise NotImplementedError("Searching by Licence Reference isn't supported yet")

    if terms.case_status:
        # This isn't always correct.
        # e.g. the "state" "Processing (FIR)" should search for applications with open requests.
        model = model.filter(status=terms.case_status)

    if terms.response_decision:
        model = model.filter(decision=terms.response_decision)

    if terms.importer_agent_name:
        name = terms.importer_agent_name
        # TODO: Revisit this when doing ICMSLST-1035
        importer_name = Q(importer__name=name)
        agent_name = Q(agent__name=name)
        model = model.filter(importer_name | agent_name)

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

    # TODO: Revisit this when doing ICMSLST-964
    # reassignment_search (searches for people not assigned to me)

    return model


def _apply_import_optimisation(model: "QuerySet[Model]") -> "QuerySet[Model]":
    """Selects related tables used for import applications."""
    model = model.select_related("importer", "contact", "application_type")

    return model


def _get_spreadsheet_rows(records: list[ImportResultRow]) -> Iterable[SpreadsheetRow]:
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
