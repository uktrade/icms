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
from web.domains.case.models import ApplicationBase

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet


@dataclass
class SearchTerms:
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


@dataclass
class SearchResults:
    total_rows: int
    records: list


class ProcessTypeAndPK(NamedTuple):
    process_type: str
    pk: int


def search_applications(terms: SearchTerms, limit: int = 200) -> SearchResults:
    """Main search function used to find applications.

    Returns records matching the supplied search terms.
    """
    app_pks_and_types = _get_search_ids_and_types(terms)

    records = []
    for queryset in _get_search_records(app_pks_and_types[:limit]):
        for rec in queryset:
            records.append(rec)

    # Sort the records by submit_datetime DESC
    records.sort(key=attrgetter("submit_datetime"), reverse=True)

    return SearchResults(total_rows=len(app_pks_and_types), records=records)


def _get_search_ids_and_types(terms: SearchTerms) -> list[ProcessTypeAndPK]:
    """Search ImportApplication records to find records matching the supplied terms.

    Returns a list of pk and process_type pairs for all matching records.
    """

    import_applications = apply_search(ImportApplication.objects.all(), terms)
    import_applications = import_applications.order_by("-submit_datetime")
    app_pks_and_types = import_applications.values_list("pk", "process_type", named=True)

    # evaluate the queryset once
    return list(app_pks_and_types)


def _get_search_records(
    search_ids_and_types: list[ProcessTypeAndPK],
) -> "Iterable[QuerySet[ApplicationBase]]":
    """Yields records matching the supplied search_ids and app types."""

    # Create a mapping of process_type -> list of app.pks
    app_pks = defaultdict(list)

    for app in search_ids_and_types:
        app_pks[app.process_type].append(app.pk)

    # Map all available process types to the function used to search those records
    pt = ImportApplicationType.ProcessTypes

    process_type_map = {
        pt.DEROGATIONS: get_derogations_applications,
        pt.FA_DFL: get_fa_dfl_applications,
        pt.FA_OIL: get_fa_oil_applications,
        pt.FA_SIL: get_fa_sil_applications,
        pt.IRON_STEEL: get_ironsteel_applications,
        pt.OPT: get_opt_applications,
        pt.SANCTIONS: get_sanctionadhoc_applications,
        pt.SPS: get_sps_applications,
        pt.TEXTILES: get_textiles_applications,
        pt.WOOD: get_wood_applications,
    }

    for pt, search_ids in app_pks.items():  # type:ignore[assignment]
        search_func = process_type_map[pt]  # type:ignore[index]

        yield search_func(search_ids)


def get_derogations_applications(search_ids: list[int]) -> "QuerySet[DerogationsApplication]":
    applications = DerogationsApplication.objects.filter(pk__in=search_ids)

    # TODO Optimise query here for template/excel download (e.g. select related)

    return applications


def get_ironsteel_applications(search_ids: list[int]) -> "QuerySet[IronSteelApplication]":
    applications = IronSteelApplication.objects.filter(pk__in=search_ids)

    # TODO Optimise query here for template/excel download (e.g. select related)

    return applications


def get_opt_applications(search_ids: list[int]) -> "QuerySet[OutwardProcessingTradeApplication]":
    applications = OutwardProcessingTradeApplication.objects.filter(pk__in=search_ids)

    # TODO Optimise query here for template/excel download (e.g. select related)

    return applications


def get_sanctionadhoc_applications(
    search_ids: list[int],
) -> "QuerySet[SanctionsAndAdhocApplication]":
    applications = SanctionsAndAdhocApplication.objects.filter(pk__in=search_ids)

    # TODO Optimise query here for template/excel download (e.g. select related)

    return applications


def get_sps_applications(search_ids: list[int]) -> "QuerySet[PriorSurveillanceApplication]":
    applications = PriorSurveillanceApplication.objects.filter(pk__in=search_ids)

    # TODO Optimise query here for template/excel download (e.g. select related)

    return applications


def get_textiles_applications(search_ids: list[int]) -> "QuerySet[TextilesApplication]":
    applications = TextilesApplication.objects.filter(pk__in=search_ids)

    # TODO Optimise query here for template/excel download (e.g. select related)

    return applications


def get_wood_applications(search_ids: list[int]) -> "QuerySet[WoodQuotaApplication]":
    applications = WoodQuotaApplication.objects.filter(pk__in=search_ids)

    # TODO Optimise query here for template/excel download (e.g. select related)

    return applications


def get_fa_oil_applications(search_ids: list[int]) -> "QuerySet[OpenIndividualLicenceApplication]":
    applications = OpenIndividualLicenceApplication.objects.filter(pk__in=search_ids)

    # TODO Optimise query here for template/excel download (e.g. select related)

    return applications


def get_fa_dfl_applications(search_ids: list[int]) -> "QuerySet[DFLApplication]":
    applications = DFLApplication.objects.filter(pk__in=search_ids)

    # TODO Optimise query here for template/excel download (e.g. select related)

    return applications


def get_fa_sil_applications(search_ids: list[int]) -> "QuerySet[SILApplication]":
    applications = SILApplication.objects.filter(pk__in=search_ids)

    # TODO Optimise query here for template/excel download (e.g. select related)

    return applications


def not_implemented_yet(terms: SearchTerms):
    raise NotImplementedError


def apply_search(model: "QuerySet[Model]", terms: SearchTerms) -> "QuerySet[Model]":
    """Apply common filtering to the supplied model - Currently just ImportApplications."""

    # THe legacy system only includes applications that have been submitted.
    model = model.exclude(submit_datetime=None)

    if terms.app_type:
        iat_filter = {"type": terms.app_type}

        if terms.app_sub_type:
            iat_filter["sub_type"] = terms.app_sub_type

        iat = ImportApplicationType.objects.get(**iat_filter)
        model = model.filter(application_type=iat)

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
