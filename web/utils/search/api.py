import datetime
from collections import defaultdict
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Iterable, Union

from django.db import models
from django.urls import reverse
from django.utils.timezone import make_aware

from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.case.export.models import ExportApplication
from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import ApplicationBase, CaseEmail, UpdateRequest
from web.domains.case.types import ImpOrExpT
from web.domains.commodity.models import Commodity
from web.domains.user.models import User
from web.flow.models import ProcessTypes
from web.models.shared import FirearmCommodity, YesNoChoices
from web.utils.spreadsheet import XlsxConfig, generate_xlsx_file

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet

    from web.domains.commodity.models import CommodityGroup
    from web.domains.country.models import Country

from . import app_data, types, utils


def search_applications(
    terms: types.SearchTerms, user: User, limit: int = 200
) -> types.SearchResults:
    """Main search function used to find applications.

    Returns records matching the supplied search terms.
    """
    app_pks_and_types = _get_search_ids_and_types(terms)

    get_result_row = _get_result_row if terms.case_type == "import" else _get_export_result_row

    records: list[types.ResultRow] = []

    for queryset in _get_search_records(app_pks_and_types[:limit]):
        for rec in queryset:
            row = get_result_row(rec, user)  # type:ignore[arg-type]
            records.append(row)  # type:ignore[arg-type]

    # Sort the records by order_by_datetime DESC (submitted date or created date)
    records.sort(key=attrgetter("order_by_datetime"), reverse=True)

    return types.SearchResults(total_rows=len(app_pks_and_types), records=records)


def get_search_results_spreadsheet(case_type: str, results: types.SearchResults) -> bytes:
    """Return a spreadsheet of the supplied search results"""

    rows: Iterable[Union[types.SpreadsheetRow, types.ExportSpreadsheetRow]]

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


def get_wildcard_filter(field: str, search_pattern: str) -> models.Q:
    """Return the filter expression for the supplied field and search_pattern.

    Strings with `%` are converted into django ORM code using one of several methods.

    :param field: The name of the field to search on
    :param search_pattern: the user supplied search pattern
    """

    if search_pattern.strip() == "%":
        return models.Q()

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

    return models.Q(**search)


# TODO: ICMSLST-1240 Add permission checks - Restrict the search to the records the user can access
def _get_search_ids_and_types(terms: types.SearchTerms) -> list[types.ProcessTypeAndPK]:
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
    search_ids_and_types: list[types.ProcessTypeAndPK],
) -> "Iterable[QuerySet[ImportApplication]]":
    """Yields records matching the supplied search_ids and app types."""

    # Create a mapping of process_type -> list of app.pks
    app_pks = defaultdict(list)

    for app in search_ids_and_types:
        app_pks[app.process_type].append(app.pk)

    # Map all available process types to the function used to search those records
    process_type_map = {
        ProcessTypes.DEROGATIONS: app_data.get_derogations_applications,
        ProcessTypes.FA_DFL: app_data.get_fa_dfl_applications,
        ProcessTypes.FA_OIL: app_data.get_fa_oil_applications,
        ProcessTypes.FA_SIL: app_data.get_fa_sil_applications,
        ProcessTypes.IRON_STEEL: app_data.get_ironsteel_applications,
        ProcessTypes.OPT: app_data.get_opt_applications,
        ProcessTypes.SANCTIONS: app_data.get_sanctionadhoc_applications,
        ProcessTypes.SPS: app_data.get_sps_applications,
        ProcessTypes.TEXTILES: app_data.get_textiles_applications,
        ProcessTypes.WOOD: app_data.get_wood_applications,
        ProcessTypes.CFS: app_data.get_cfs_applications,
        ProcessTypes.COM: app_data.get_com_applications,
        ProcessTypes.GMP: app_data.get_gmp_applications,
    }

    for app_pt, search_ids in app_pks.items():  # type:ignore[assignment]
        search_func = process_type_map[app_pt]  # type:ignore[index]

        yield search_func(search_ids)


def _get_result_row(rec: ImportApplication, user: User) -> types.ImportResultRow:
    """Process the incoming application and return a result row."""

    start_date = rec.licence_start_date.strftime("%d %b %Y") if rec.licence_start_date else None
    end_date = rec.licence_end_date.strftime("%d %b %Y") if rec.licence_end_date else None
    licence_validity = " - ".join(filter(None, (start_date, end_date)))

    licence_reference = _get_licence_reference(rec)
    commodity_details = app_data.get_commodity_details(rec)

    if rec.application_type.type == rec.application_type.Types.FIREARMS:
        application_subtype = rec.application_type.get_sub_type_display()
    else:
        application_subtype = ""

    cus = rec.get_chief_usage_status_display() if rec.chief_usage_status else None

    # TODO: Revisit when implementing ICMSLST-1169
    assignee_title = "Application Processing (IMA3) / Case Officer"
    ownership_date = "05-Oct-2021 09:39"
    assignee_name = f"{rec.case_owner.full_name} ({rec.case_owner.email})" if rec.case_owner else ""
    reassignment_date = "11-Oct-2021 14:52"

    row = types.ImportResultRow(
        app_pk=rec.pk,
        submitted_at=rec.submit_datetime.strftime("%d %b %Y %H:%M:%S"),
        case_status=types.CaseStatus(
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
        applicant_details=types.ApplicantDetails(
            organisation_name=rec.importer.name,
            agent_name=rec.agent.name if rec.agent else None,
            application_contact=rec.contact.full_name,
        ),
        commodity_details=commodity_details,
        assignee_details=types.AssigneeDetails(
            title=assignee_title,
            ownership_date=ownership_date,
            assignee_name=assignee_name,
            reassignment_date=reassignment_date,
        ),
        actions=get_import_record_actions(rec, user),
        order_by_datetime=rec.order_by_datetime,  # This is an annotation
    )

    return row


def _get_export_result_row(rec: ExportApplication, user: User) -> types.ExportResultRow:
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

    # TODO: Revisit when implementing ICMSLST-1169
    # assignee_title = "Authorise Documents (G2) / Authoriser"
    assignee_title = "Application Processing (CA50) / Case Officer"
    ownership_date = "05-Oct-2021 09:39"
    assignee_name = f"{rec.case_owner.full_name} ({rec.case_owner.email})" if rec.case_owner else ""
    reassignment_date = "11-Oct-2021 14:52"

    return types.ExportResultRow(
        app_pk=rec.pk,
        case_reference=rec.get_reference(),
        application_type=app_type_label,
        status=rec.get_status_display(),
        certificates=certificates,
        origin_countries=origin_countries,
        organisation_name=rec.exporter.name,
        application_contact=application_contact,
        submitted_at=submitted_at,
        manufacturer_countries=manufacturer_countries,
        assignee_details=types.AssigneeDetails(
            title=assignee_title,
            ownership_date=ownership_date,
            assignee_name=assignee_name,
            reassignment_date=reassignment_date,
        ),
        agent_name=rec.agent.name if rec.agent else None,
        actions=get_export_record_actions(rec, user),
        order_by_datetime=rec.order_by_datetime,  # This is an annotation
    )


def _get_certificate_references(rec: ExportApplication) -> list[str]:
    """Retrieve the certificate references."""

    # TODO: Revisit when implementing ICMSLST-1223
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


def _apply_search(model: "QuerySet[Model]", terms: types.SearchTerms) -> "QuerySet[Model]":
    """Apply all search terms for Import and Export applications."""

    # THe legacy system only includes applications that have been submitted.
    if terms.case_type == "import":
        model = model.filter(submit_datetime__isnull=False)

    if terms.reassignment_search:
        model = model.filter(
            case_owner__isnull=False,
            status__in=[
                ApplicationBase.Statuses.PROCESSING,
                ApplicationBase.Statuses.VARIATION_REQUESTED,
            ],
        )

        if terms.reassignment_user:
            model = model.filter(case_owner=terms.reassignment_user)

    if terms.app_type:
        key = "type" if terms.case_type == "import" else "type_code"
        iat_filter = {f"application_type__{key}": terms.app_type}

        if terms.app_sub_type:
            iat_filter["application_type__sub_type"] = terms.app_sub_type

        model = model.filter(**iat_filter)

    if terms.case_ref:
        reference_filter = get_wildcard_filter("reference", terms.case_ref)
        model = model.filter(reference_filter)

    if terms.licence_ref:
        # TODO: Revisit when implementing ICMSLST-1048
        # Need to wildcard match on the licence_reference field for Import Application's

        # TODO: Revisit when implementing ICMSLST-1223
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

        model = model.filter(first_name_filter | last_name_filter)

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

    model = model.annotate(order_by_datetime=utils.get_order_by_datetime(terms.case_type))

    return model


def _get_status_to_filter(case_type: str, case_status: str) -> models.Q:
    if case_type == "import":
        choices = dict(get_import_status_choices())
    else:
        choices = dict(get_export_status_choices())

    if case_status not in choices:
        raise NotImplementedError(f"Filter ({case_status}) for case status not supported.")

    if case_status == "FIR_REQUESTED":
        filters = models.Q(further_information_requests__status=FurtherInformationRequest.OPEN)
    elif case_status == "UPDATE_REQUESTED":
        filters = models.Q(update_requests__status=UpdateRequest.Status.OPEN)
    elif case_status == "BEIS":
        filters = models.Q(
            certificateofgoodmanufacturingpracticeapplication__case_emails__status=CaseEmail.Status.OPEN
        )
    elif case_status == "HSE":
        filters = models.Q(
            certificateoffreesaleapplication__case_emails__status=CaseEmail.Status.OPEN
        )
    else:
        filters = models.Q(status=case_status)

    return filters


def _apply_import_application_filter(
    model: "QuerySet[Model]", terms: types.SearchTerms
) -> "QuerySet[Model]":

    if terms.applicant_ref:
        applicant_ref_filter = get_wildcard_filter("applicant_reference", terms.applicant_ref)
        model = model.filter(applicant_ref_filter)

    if terms.importer_agent_name:
        importer_filter = get_wildcard_filter("importer__name", terms.importer_agent_name)
        agent_filter = get_wildcard_filter("agent__name", terms.importer_agent_name)

        model = model.filter(importer_filter | agent_filter)

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
        ironsteel_query = models.Q(ironsteelapplication__shipping_year=terms.shipping_year)
        textiles_query = models.Q(textilesapplication__shipping_year=terms.shipping_year)
        wood_query = models.Q(woodquotaapplication__shipping_year=terms.shipping_year)

        model = model.filter(ironsteel_query | textiles_query | wood_query)

    if terms.goods_category:
        model = model.filter(_get_goods_category_filter(terms))

    if terms.commodity_code:
        commodity_filter = _get_commodity_code_filter(terms)
        model = model.filter(commodity_filter)

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


def _get_goods_category_filter(terms: types.SearchTerms) -> models.Q:
    """Return the goods_category filter for the applications that support it.

    :param terms: Search terms
    """

    good_category: "CommodityGroup" = terms.goods_category  # type: ignore[assignment]

    if good_category.group_name in FirearmCommodity:  # type: ignore[operator]
        fa_dfl_query = models.Q(dflapplication__commodity_code=good_category.group_name)
        fa_oil_query = models.Q(
            openindividuallicenceapplication__commodity_code=good_category.group_name
        )
        fa_sil_query = models.Q(silapplication__commodity_code=good_category.group_name)

        filter_query = fa_dfl_query | fa_oil_query | fa_sil_query

    else:
        ironsteel_query = models.Q(ironsteelapplication__category_commodity_group=good_category)
        textiles_query = models.Q(textilesapplication__category_commodity_group=good_category)
        opt_query = models.Q(
            outwardprocessingtradeapplication__cp_category=good_category.group_code
        )

        filter_query = ironsteel_query | textiles_query | opt_query

    return filter_query


def _get_commodity_code_filter(terms: types.SearchTerms) -> models.Q:
    """Return the commodity code filter expression for the applications that support it.

    :param terms: Search terms
    """

    if not terms.commodity_code or terms.commodity_code.strip() == "%":
        return models.Q()

    commodity_filter = get_wildcard_filter("commodity_code", terms.commodity_code)
    matching_commodiy_ids = list(
        Commodity.objects.filter(commodity_filter).values_list("pk", flat=True)
    )

    applications: dict[Any, list[str]] = {
        ImportApplicationType.Types.DEROGATION: ["derogationsapplication__commodity"],
        ImportApplicationType.Types.FIREARMS: [],  # Firearm apps don't have commodities to filter
        ImportApplicationType.Types.IRON_STEEL: ["ironsteelapplication__commodity"],
        ImportApplicationType.Types.OPT: [
            "outwardprocessingtradeapplication__cp_commodities",
            "outwardprocessingtradeapplication__teg_commodities",
        ],
        ImportApplicationType.Types.SANCTION_ADHOC: [
            "sanctionsandadhocapplication__sanctionsandadhocapplicationgoods__commodity"
        ],
        ImportApplicationType.Types.SPS: [
            "priorsurveillanceapplication__commodity",
        ],
        ImportApplicationType.Types.TEXTILES: [
            "textilesapplication__commodity",
        ],
        ImportApplicationType.Types.WOOD_QUOTA: ["woodquotaapplication__commodity"],
    }

    commodity_code_filter = models.Q()
    if terms.app_type:
        apps: list[str] = applications[terms.app_type]  # type: ignore[index]

        for field in apps:
            commodity_code_filter |= models.Q(**{f"{field}__in": matching_commodiy_ids})

    else:
        for app_filters in applications.values():
            for field in app_filters:
                commodity_code_filter |= models.Q(**{f"{field}__in": matching_commodiy_ids})

    return commodity_code_filter


def _apply_export_application_filter(
    model: "QuerySet[Model]", terms: types.SearchTerms
) -> "QuerySet[Model]":
    if terms.exporter_agent_name:
        exporter_filter = get_wildcard_filter("exporter__name", terms.exporter_agent_name)
        agent_filter = get_wildcard_filter("agent__name", terms.exporter_agent_name)

        model = model.filter(exporter_filter | agent_filter)

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


def _get_country_filter(country_qs: "QuerySet[Country]", field: str) -> dict[str, Any]:
    if country_qs.count() == 1:
        country_filter = {field: country_qs.first()}
    else:
        country_filter = {f"{field}__in": country_qs}

    return country_filter


def _get_import_spreadsheet_rows(
    records: list[types.ImportResultRow],
) -> Iterable[types.SpreadsheetRow]:
    """Converts the incoming records in to a spreadsheet row."""

    for row in records:
        cs = row.case_status
        ad = row.applicant_details
        cd = row.commodity_details

        commodity_codes = ", ".join(cd.commodity_codes) if cd.commodity_codes else None

        yield types.SpreadsheetRow(
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


def _get_export_spreadsheet_rows(
    records: list[types.ExportResultRow],
) -> Iterable[types.ExportSpreadsheetRow]:
    for row in records:
        certificates = ", ".join(row.certificates)
        certificate_countries = ", ".join(row.origin_countries)
        manufacturer_countries = ", ".join(row.manufacturer_countries)

        yield types.ExportSpreadsheetRow(
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


def get_import_record_actions(rec: "ImportApplication", user: User) -> list[types.SearchAction]:
    """Get the available actions for the supplied import application.

    :param rec: Import Application record.
    :param user: User performing search
    """
    st = ImportApplication.Statuses
    actions = []

    # TODO: ICMSLST-1240: Add actions for Exporter / Exporter agents
    # Standard User (importer/agent) actions:
    #   Status = COMPLETED
    #       Request Variation

    if rec.status == ImportApplication.Statuses.COMPLETED:
        # TODO: ICMSLST-686
        actions.append(
            types.SearchAction(
                url=reverse(
                    "case:search-request-variation",
                    kwargs={"application_pk": rec.pk, "case_type": "import"},
                ),
                name="request-variation",
                label="Request Variation",
                icon="icon-redo2",
                is_post=False,
            )
        )

        if rec.decision == rec.REFUSE:
            # TODO: ICMSLST-1001
            actions.append(
                types.SearchAction(
                    url="#", name="manage-appeals", label="Manage Appeals", icon="icon-warning"
                )
            )

        if rec.licence_end_date and rec.licence_end_date > datetime.date.today():
            # TODO: ICMSLST-999
            actions.append(
                types.SearchAction(
                    url="#", name="revoke-licence", label="Revoke Licence", icon="icon-undo2"
                )
            )

    elif rec.status in [st.STOPPED, st.WITHDRAWN]:
        actions.append(
            types.SearchAction(
                url=reverse(
                    "case:search-reopen-case",
                    kwargs={"application_pk": rec.pk, "case_type": "import"},
                ),
                name="reopen-case",
                label="Reopen Case",
                icon="icon-redo2",
            )
        )

    return actions


def get_export_record_actions(rec: "ExportApplication", user: User) -> list[types.SearchAction]:
    """Get the available actions for the supplied export application.

    :param rec: Export Application record.
    :param user: User performing search
    """

    st = ExportApplication.Statuses
    actions: list[types.SearchAction] = []

    # TODO: ICMSLST-1240: Add actions for Exporter / Exporter agents
    # Exporter / Exporter’s Agent actions:
    #   Status != STOPPED or WITHDRAWN:
    #       Copy Application
    #       Create Template

    if rec.status == st.COMPLETED:
        # TODO: ICMSLST-1005
        actions.append(
            types.SearchAction(
                url="#", name="open-variation", label="Open Variation", icon="icon-redo2"
            )
        )

        # TODO: ICMSLST-1006
        # TODO: Revisit when implementing ICMSLST-1223
        # Determine whether the Revoke Certificates should appear or not
        actions.append(
            types.SearchAction(
                url="#", name="revoke-certificates", label="Revoke Certificates", icon="icon-undo2"
            )
        )

    if rec.status in [st.STOPPED, st.WITHDRAWN]:
        # TODO: ICMSLST-1213
        actions.append(
            types.SearchAction(url="#", name="reopen-case", label="Reopen Case", icon="icon-redo2")
        )
    else:
        # TODO: ICMSLST-1002/ICMSLST-1226 (Depending on which ticket we do)
        actions.append(
            types.SearchAction(
                url="#", name="copy-application", label="Copy Application", icon="icon-copy"
            )
        )

        # TODO: ICMSLST-1241
        actions.append(
            types.SearchAction(
                url="#", name="create-template", label="Create Template", icon="icon-magic-wand"
            )
        )

    return actions
