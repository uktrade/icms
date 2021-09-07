import datetime
from collections import defaultdict
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING, Iterable, NamedTuple, Optional

from django.db.models import Q

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
    submitted_datetime_start: Optional[datetime.datetime] = None
    submitted_datetime_end: Optional[datetime.datetime] = None
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
    applicant_reference: Optional[str] = None
    licence_reference: Optional[str] = None
    licence_validity: Optional[str] = None


@dataclass
class ApplicantDetails:
    organisation_name: str
    application_contact: str


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
        ),
        applicant_details=ApplicantDetails(
            organisation_name=rec.importer.name,
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
    if rec.process_type == ImportApplicationType.ProcessTypes.WOOD:
        app: WoodQuotaApplication = rec

        details = CommodityDetails(
            origin_country="None",  # This is to match legacy for this application type
            shipping_year=app.shipping_year,
            commodity_codes=[app.commodity.commodity_code],
        )

    else:
        # TODO ICMSLST-1049: Replace hardcoded values with application specific versions
        details = CommodityDetails(
            origin_country="Iran",
            consignment_country="Algeria",
            goods_category="ex Chapter 93",
            shipping_year=2021,
            commodity_codes=["2801000010", "2850002070"],
        )

    return details


def _get_derogations_applications(search_ids: list[int]) -> "QuerySet[DerogationsApplication]":
    applications = DerogationsApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    return applications


def _get_ironsteel_applications(search_ids: list[int]) -> "QuerySet[IronSteelApplication]":
    applications = IronSteelApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    return applications


def _get_opt_applications(search_ids: list[int]) -> "QuerySet[OutwardProcessingTradeApplication]":
    applications = OutwardProcessingTradeApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    return applications


def _get_sanctionadhoc_applications(
    search_ids: list[int],
) -> "QuerySet[SanctionsAndAdhocApplication]":
    applications = SanctionsAndAdhocApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    return applications


def _get_sps_applications(search_ids: list[int]) -> "QuerySet[PriorSurveillanceApplication]":
    applications = PriorSurveillanceApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    return applications


def _get_textiles_applications(search_ids: list[int]) -> "QuerySet[TextilesApplication]":
    applications = TextilesApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    return applications


def _get_wood_applications(search_ids: list[int]) -> "QuerySet[WoodQuotaApplication]":
    applications = WoodQuotaApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)
    applications = applications.select_related("commodity")

    return applications


def _get_fa_oil_applications(search_ids: list[int]) -> "QuerySet[OpenIndividualLicenceApplication]":
    applications = OpenIndividualLicenceApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    return applications


def _get_fa_dfl_applications(search_ids: list[int]) -> "QuerySet[DFLApplication]":
    applications = DFLApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    return applications


def _get_fa_sil_applications(search_ids: list[int]) -> "QuerySet[SILApplication]":
    applications = SILApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

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

    if terms.submitted_datetime_start:
        model = model.filter(submit_datetime__gte=terms.submitted_datetime_start)

    if terms.submitted_datetime_end:
        model = model.filter(submit_datetime__lte=terms.submitted_datetime_end)

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
