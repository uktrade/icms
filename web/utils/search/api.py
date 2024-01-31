import datetime as dt
from collections import defaultdict
from collections.abc import Iterable
from operator import attrgetter
from typing import Any

from django.db import models
from django.db.models import Model, QuerySet
from django.urls import reverse
from django.utils import timezone

from web.domains.case.models import DocumentPackBase
from web.domains.case.shared import ImpExpStatus
from web.flow.models import ProcessTypes
from web.models import (
    CaseDocumentReference,
    CaseEmail,
    Commodity,
    CommodityGroup,
    Country,
    ExportApplication,
    FurtherInformationRequest,
    ImportApplication,
    ImportApplicationType,
    UpdateRequest,
    User,
)
from web.models.shared import FirearmCommodity, YesNoChoices
from web.utils.spreadsheet import XlsxSheetConfig, generate_xlsx_file

from . import app_data, types, utils
from .actions import get_export_record_actions, get_import_record_actions


def search_applications(
    terms: types.SearchTerms, user: User, limit: int = 200
) -> types.SearchResults:
    """Main search function used to find applications.

    Return records matching the supplied search terms.
    """
    app_pks_and_types = _get_search_ids_and_types(terms, user)

    get_result_row = _get_result_row if terms.case_type == "import" else _get_export_result_row

    records: list[types.ResultRow] = []

    user_org_perms = utils.UserOrganisationPermissions(user, terms.case_type)
    for queryset in _get_search_records(app_pks_and_types[:limit]):
        for rec in queryset:
            row = get_result_row(rec, user_org_perms)
            records.append(row)  # type:ignore[arg-type]

    # Sort the records by order_by_datetime DESC (submitted date or created date)
    records.sort(key=attrgetter("order_by_datetime"), reverse=True)

    return types.SearchResults(total_rows=len(app_pks_and_types), records=records)


def get_search_results_spreadsheet(case_type: str, results: types.SearchResults) -> bytes:
    """Return a spreadsheet of the supplied search results"""

    rows: Iterable[types.SpreadsheetRow | types.ExportSpreadsheetRow]

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

    config = XlsxSheetConfig()
    config.header.data = header_data
    config.header.styles = {"bold": True}
    config.rows = rows  # type: ignore[assignment]
    config.column_width = 25
    config.sheet_name = "Sheet 1"

    return generate_xlsx_file([config])


def get_import_status_choices() -> list[tuple[Any, str]]:
    st = ImportApplication.Statuses

    return [
        (st.COMPLETED.value, st.COMPLETED.label),
        (st.PROCESSING.value, st.PROCESSING.label),
        ("FIR_REQUESTED", "Processing (FIR)"),
        ("UPDATE_REQUESTED", "Processing (Update)"),
        (st.REVOKED.value, st.REVOKED.label),
        (st.STOPPED.value, st.STOPPED.label),
        (st.SUBMITTED.value, st.SUBMITTED.label),
        (st.VARIATION_REQUESTED.value, st.VARIATION_REQUESTED.label),
        (st.WITHDRAWN.value, st.WITHDRAWN.label),
    ]


def get_export_status_choices() -> list[tuple[Any, str]]:
    st = ExportApplication.Statuses

    return [
        (st.COMPLETED.value, st.COMPLETED.label),
        (st.IN_PROGRESS.value, st.IN_PROGRESS.label),
        (st.PROCESSING.value, st.PROCESSING.label),
        ("BEIS", "Processing (BEIS)"),
        ("FIR_REQUESTED", "Processing (FIR)"),
        ("HSE", "Processing (HSE)"),
        ("UPDATE_REQUESTED", "Processing (Update)"),
        (st.REVOKED.value, st.REVOKED.label),
        (st.STOPPED.value, st.STOPPED.label),
        (st.SUBMITTED.value, st.SUBMITTED.label),
        (st.VARIATION_REQUESTED.value, st.VARIATION_REQUESTED.label),
        (st.WITHDRAWN.value, st.WITHDRAWN.label),
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


def _get_search_ids_and_types(terms: types.SearchTerms, user: User) -> list[types.ProcessTypeAndPK]:
    """Search ImportApplication records to find records matching the supplied terms.

    Returns a list of pk and process_type pairs for all matching records.
    """

    if terms.case_type == "import":
        applications = utils.get_user_import_applications(user)
    else:
        applications = utils.get_user_export_applications(user)

    applications = _apply_search(applications, terms)
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

    for app_pt, search_ids in app_pks.items():
        search_func = process_type_map[app_pt]  # type:ignore[index]

        yield search_func(search_ids)


def _get_result_row(
    rec: ImportApplication, user_org_perms: utils.UserOrganisationPermissions
) -> types.ImportResultRow:
    """Process the incoming application and return a result row."""

    start_date = (
        rec.latest_licence_start_date.strftime("%d %b %Y")
        if rec.latest_licence_start_date
        else None
    )
    end_date = (
        rec.latest_licence_end_date.strftime("%d %b %Y") if rec.latest_licence_end_date else None
    )
    licence_validity = " - ".join(filter(None, (start_date, end_date)))

    commodity_details = app_data.get_commodity_details(rec)

    if rec.application_type.type == rec.application_type.Types.FIREARMS:
        application_subtype = rec.application_type.get_sub_type_display()
    else:
        application_subtype = ""

    cus = rec.get_chief_usage_status_display() if rec.chief_usage_status else None

    row = types.ImportResultRow(
        app_pk=rec.pk,
        submitted_at=rec.submit_datetime.strftime("%d %b %Y %H:%M:%S"),
        case_status=types.CaseStatus(
            applicant_reference=getattr(rec, "applicant_reference", ""),
            case_reference=rec.get_reference(),
            licence_reference=_get_licence_reference(rec),
            licence_reference_link=_get_licence_reference_link(rec),
            licence_validity=licence_validity,
            application_type=rec.application_type.get_type_display(),
            application_sub_type=application_subtype,
            status=rec.get_status_display(),
            licence_type="Paper" if rec.latest_licence_issue_paper_licence_only else "Electronic",
            chief_usage_status=cus,
            licence_start_date=start_date,
            licence_end_date=end_date,
        ),
        applicant_details=types.ApplicantDetails(
            organisation_name=rec.importer.name,
            agent_name=rec.agent.name if rec.agent else None,
            application_contact=rec.contact.full_name,
        ),
        commodity_details=commodity_details,
        assignee_details=_get_assignee_details(rec),
        actions=get_import_record_actions(rec, user_org_perms),
        order_by_datetime=rec.order_by_datetime,  # This is an annotation
    )

    return row


def _get_export_result_row(
    rec: ExportApplication, user_org_permissions: utils.UserOrganisationPermissions
) -> types.ExportResultRow:
    app_type_label = ProcessTypes(rec.process_type).label
    application_contact = rec.contact.full_name if rec.contact else ""
    submitted_at = rec.submit_datetime.strftime("%d %b %Y %H:%M:%S") if rec.submit_datetime else ""

    manufacturer_countries = []
    if rec.process_type == ProcessTypes.CFS:
        # Can be None or a list of country names (can contain None for empty schedules)
        if rec.manufacturer_countries:
            manufacturer_countries = [c for c in rec.manufacturer_countries if c]

    # This is an annotation and can have a value of [None] for in-progress apps
    origin_countries = [c for c in rec.origin_countries if c]

    return types.ExportResultRow(
        app_pk=rec.pk,
        case_reference=rec.get_reference(),
        application_type=app_type_label,
        status=rec.get_status_display(),
        certificates=_get_certificate_references_and_links(rec),
        origin_countries=origin_countries,
        organisation_name=rec.exporter.name,
        application_contact=application_contact,
        submitted_at=submitted_at,
        manufacturer_countries=manufacturer_countries,
        assignee_details=_get_assignee_details(rec),
        agent_name=rec.agent.name if rec.agent else None,
        actions=get_export_record_actions(rec, user_org_permissions),
        order_by_datetime=rec.order_by_datetime,  # This is an annotation
    )


def _get_assignee_details(app: ImportApplication | ExportApplication) -> types.AssigneeDetails:
    assignee_name = f"{app.case_owner.full_name} ({app.case_owner.email})" if app.case_owner else ""
    reassignment_at = (
        app.reassign_datetime.strftime("%d %b %Y %H:%M") if app.reassign_datetime else ""
    )
    submitted_at = app.submit_datetime.strftime("%d %b %Y %H:%M") if app.submit_datetime else ""

    return types.AssigneeDetails(
        title="Case Officer",
        ownership_date=submitted_at,
        assignee_name=assignee_name,
        reassignment_date=reassignment_at,
    )


def _get_licence_reference(rec: ImportApplication) -> str:
    """Get the licence reference for the import application licence."""

    if not rec.latest_licence_cdr_data or rec.status != ImpExpStatus.COMPLETED:
        return ""

    # Example value: [[8, 'GBSIL0000004E']]
    _, reference = rec.latest_licence_cdr_data[0]

    if rec.latest_licence_issue_paper_licence_only:
        return f"{reference} (Paper)"
    else:
        return f"{reference} (Electronic)"


def _get_licence_reference_link(rec: ImportApplication) -> str:
    """Get the licence reference link for the import application licence."""

    if not rec.latest_licence_cdr_data or rec.status != ImpExpStatus.COMPLETED:
        return "#"

    # Example value: [[8, 'GBSIL0000004E']]
    casedocumentreference_pk, _ = rec.latest_licence_cdr_data[0]

    return reverse(
        "case:view-case-document",
        kwargs={
            "application_pk": rec.id,
            "case_type": "import",
            "object_pk": rec.latest_licence_pk,
            "casedocumentreference_pk": casedocumentreference_pk,
        },
    )


def _get_certificate_references_and_links(rec: ExportApplication) -> list[tuple[str, str]]:
    """Return a list of reference / url pairs for the export application certificate.

    :param rec: Export Application
    """
    if not rec.latest_certificate_references or rec.status not in [
        ImpExpStatus.COMPLETED,
        ImpExpStatus.REVOKED,
    ]:
        return []

    # The below code will be correct when we have certificate files uploaded to S3
    # Uncomment when the export certificate documents have been created.
    return [
        (
            reference,
            reverse(
                "case:view-case-document",
                kwargs={
                    "application_pk": rec.id,
                    "case_type": "export",
                    "object_pk": rec.latest_certificate_pk,
                    "casedocumentreference_pk": cdr_pk,
                },
            ),
        )
        for (cdr_pk, reference) in rec.latest_certificate_references
    ]


def _apply_search(model: QuerySet[Model], terms: types.SearchTerms) -> QuerySet[Model]:
    """Apply all search terms for Import and Export applications."""

    # THe legacy system only includes applications that have been submitted.
    if terms.case_type == "import":
        model = model.filter(submit_datetime__isnull=False)

    if terms.reassignment_search:
        model = model.filter(
            case_owner__isnull=False,
            status__in=[ImpExpStatus.PROCESSING, ImpExpStatus.VARIATION_REQUESTED],
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
        if terms.case_type == "import":
            licence_filter = get_wildcard_filter(
                "licences__document_references__reference", terms.licence_ref
            )
            model = model.filter(
                licence_filter,
                licences__document_references__document_type=CaseDocumentReference.Type.LICENCE,
                licences__status__in=[
                    DocumentPackBase.Status.DRAFT,
                    DocumentPackBase.Status.ACTIVE,
                ],
            )

        else:
            licence_filter = get_wildcard_filter(
                "certificates__document_references__reference", terms.licence_ref
            )
            model = model.filter(
                licence_filter,
                certificates__document_references__document_type=CaseDocumentReference.Type.CERTIFICATE,
                certificates__status__in=[
                    DocumentPackBase.Status.DRAFT,
                    DocumentPackBase.Status.ACTIVE,
                ],
            )

    if terms.case_status:
        filters = _get_status_to_filter(terms.case_type, terms.case_status)
        model = model.filter(filters)

    if terms.response_decision:
        model = model.filter(decision=terms.response_decision)

    if terms.submitted_date_start:
        start_datetime = timezone.make_aware(
            dt.datetime.combine(terms.submitted_date_start, dt.datetime.min.time())
        )

        model = model.filter(submit_datetime__gte=start_datetime)

    if terms.submitted_date_end:
        end_datetime = timezone.make_aware(
            dt.datetime.combine(terms.submitted_date_end, dt.datetime.max.time())
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
    model: QuerySet[Model], terms: types.SearchTerms
) -> QuerySet[Model]:
    if terms.applicant_ref:
        applicant_ref_filter = get_wildcard_filter("applicant_reference", terms.applicant_ref)
        model = model.filter(applicant_ref_filter)

    if terms.importer_agent_name:
        importer_filter = get_wildcard_filter("importer__name", terms.importer_agent_name)
        agent_filter = get_wildcard_filter("agent__name", terms.importer_agent_name)

        model = model.filter(importer_filter | agent_filter)

    if terms.licence_type:
        paper_only = terms.licence_type == "paper"
        model = model.filter(
            licences__status__in=[
                DocumentPackBase.Status.DRAFT,
                DocumentPackBase.Status.ACTIVE,
            ],
            licences__issue_paper_licence_only=paper_only,
        )

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

    if terms.licence_date_start:
        model = model.filter(
            licences__status__in=[
                DocumentPackBase.Status.DRAFT,
                DocumentPackBase.Status.ACTIVE,
            ],
            licences__licence_start_date__gte=terms.licence_date_start,
        )

    if terms.licence_date_end:
        model = model.filter(
            licences__status__in=[
                DocumentPackBase.Status.DRAFT,
                DocumentPackBase.Status.ACTIVE,
            ],
            licences__licence_end_date__lte=terms.licence_date_end,
        )

    if terms.issue_date_start:
        start_datetime = timezone.make_aware(
            dt.datetime.combine(terms.issue_date_start, dt.datetime.min.time())
        )

        model = model.filter(
            licences__status=DocumentPackBase.Status.ACTIVE,
            licences__case_completion_datetime__gte=start_datetime,
        )

    if terms.issue_date_end:
        end_datetime = timezone.make_aware(
            dt.datetime.combine(terms.issue_date_end, dt.datetime.max.time())
        )

        model = model.filter(
            licences__status=DocumentPackBase.Status.ACTIVE,
            licences__case_completion_datetime__lte=end_datetime,
        )

    return model


def _get_goods_category_filter(terms: types.SearchTerms) -> models.Q:
    """Return the goods_category filter for the applications that support it.

    :param terms: Search terms
    """

    good_category: "CommodityGroup" = terms.goods_category  # type: ignore[assignment]

    if good_category.group_name in FirearmCommodity:
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
            "sanctionsandadhocapplication__sanctions_goods__commodity"
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
        apps: list[str] = applications[terms.app_type]

        for field in apps:
            commodity_code_filter |= models.Q(**{f"{field}__in": matching_commodiy_ids})

    else:
        for app_filters in applications.values():
            for field in app_filters:
                commodity_code_filter |= models.Q(**{f"{field}__in": matching_commodiy_ids})

    return commodity_code_filter


def _apply_export_application_filter(
    model: QuerySet[Model], terms: types.SearchTerms
) -> QuerySet[Model]:
    if terms.exporter_agent_name:
        exporter_filter = get_wildcard_filter("exporter__name", terms.exporter_agent_name)
        agent_filter = get_wildcard_filter("agent__name", terms.exporter_agent_name)

        model = model.filter(exporter_filter | agent_filter)

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


def _get_country_filter(country_qs: QuerySet[Country], field: str) -> dict[str, Any]:
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
        # c is a two element tuple (certificate reference, certificate link)
        certificates = ", ".join(c[0] for c in row.certificates)
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
