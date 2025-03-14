from typing import TYPE_CHECKING

from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.aggregates import ArrayAgg, JSONBAgg
from django.db.models import F, FilteredRelation, Func, OuterRef, Q, Subquery, Value
from django.db.models.expressions import RawSQL
from django.db.models.functions import Coalesce

from web.flow.models import ProcessTypes
from web.models import (
    CaseDocumentReference,
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    CFSSchedule,
    DFLApplication,
    ExportApplication,
    ExportApplicationCertificate,
    ImportApplication,
    ImportApplicationLicence,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    PriorSurveillanceApplication,
    SanctionsAndAdhocApplication,
    SanctionsAndAdhocApplicationGoods,
    SILApplication,
    TextilesApplication,
    WoodQuotaApplication,
)

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet

from . import types, utils


def get_fa_dfl_applications(search_ids: list[int]) -> "QuerySet[DFLApplication]":
    applications = DFLApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related(
        "origin_country", "consignment_country", "supplementary_info"
    )

    applications = _add_import_licence_data(applications)

    return applications


def get_fa_oil_applications(search_ids: list[int]) -> "QuerySet[OpenIndividualLicenceApplication]":
    applications = OpenIndividualLicenceApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related(
        "origin_country", "consignment_country", "supplementary_info"
    )

    applications = _add_import_licence_data(applications)

    return applications


def get_fa_sil_applications(search_ids: list[int]) -> "QuerySet[SILApplication]":
    applications = SILApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related(
        "origin_country", "consignment_country", "supplementary_info"
    )

    applications = _add_import_licence_data(applications)

    return applications


def get_opt_applications(search_ids: list[int]) -> "QuerySet[OutwardProcessingTradeApplication]":
    applications = OutwardProcessingTradeApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related("cp_origin_country", "cp_processing_country")

    CpCommodities = OutwardProcessingTradeApplication.cp_commodities.through
    TegCommodities = OutwardProcessingTradeApplication.teg_commodities.through

    cp_commodity_codes_sq = (
        CpCommodities.objects.filter(outwardprocessingtradeapplication_id=OuterRef("pk"))
        .order_by()
        .values("outwardprocessingtradeapplication")
        .annotate(commodity_array=ArrayAgg("commodity__commodity_code", default=Value([])))
        .values("commodity_array")
    )

    teg_commodity_codes_sq = (
        TegCommodities.objects.filter(outwardprocessingtradeapplication_id=OuterRef("pk"))
        .order_by()
        .values("outwardprocessingtradeapplication")
        .annotate(commodity_array=ArrayAgg("commodity__commodity_code", default=Value([])))
        .values("commodity_array")
    )

    # Create a default value for historic records that don't have cp / teg commodities
    default_sub_query_val = RawSQL("'{}'", [])
    applications = applications.annotate(
        cp_commodity_codes=Coalesce(Subquery(cp_commodity_codes_sq), default_sub_query_val),
        teg_commodity_codes=Coalesce(Subquery(teg_commodity_codes_sq), default_sub_query_val),
    )

    applications = _add_import_licence_data(applications)

    return applications


# TODO: Extend with NuclearMaterialApplication
def get_sanctionadhoc_applications(
    search_ids: list[int],
) -> "QuerySet[SanctionsAndAdhocApplication]":
    applications = SanctionsAndAdhocApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related("origin_country", "consignment_country")

    # Need to annotate using the subquery now we are using `DISTINCT ON`
    # https://docs.djangoproject.com/en/4.0/ref/models/expressions/#using-aggregates-within-a-subquery-expression
    commodity_codes_sub_query = (
        SanctionsAndAdhocApplicationGoods.objects.filter(import_application_id=OuterRef("id"))
        .order_by()
        .values("import_application")
        .annotate(
            commodity_array=ArrayAgg("commodity__commodity_code", distinct=True, default=Value([]))
        )
        .values("commodity_array")
    )
    applications = applications.annotate(commodity_codes=Subquery(commodity_codes_sub_query))

    applications = _add_import_licence_data(applications)

    return applications


def get_sps_applications(search_ids: list[int]) -> "QuerySet[PriorSurveillanceApplication]":
    applications = PriorSurveillanceApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related("origin_country", "consignment_country", "commodity")

    applications = _add_import_licence_data(applications)

    return applications


def get_textiles_applications(search_ids: list[int]) -> "QuerySet[TextilesApplication]":
    applications = TextilesApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)

    applications = applications.select_related(
        "origin_country", "consignment_country", "category_commodity_group", "commodity"
    )

    applications = _add_import_licence_data(applications)

    return applications


def get_wood_applications(search_ids: list[int]) -> "QuerySet[WoodQuotaApplication]":
    applications = WoodQuotaApplication.objects.filter(pk__in=search_ids)
    applications = _apply_import_optimisation(applications)
    applications = applications.select_related("commodity")

    applications = _add_import_licence_data(applications)

    return applications


def get_cfs_applications(search_ids: list[int]) -> "QuerySet[CertificateOfFreeSaleApplication]":
    applications = CertificateOfFreeSaleApplication.objects.filter(pk__in=search_ids)
    applications = _apply_export_optimisation(applications)

    manufacturer_countries_sub_query = (
        CFSSchedule.objects.filter(application_id=OuterRef("id"))
        .order_by()
        .values("application")
        .annotate(
            manufacturer_countries_array=ArrayAgg(
                "country_of_manufacture__name", distinct=True, default=Value([])
            )
        )
        .values("manufacturer_countries_array")
    )
    applications = applications.annotate(
        manufacturer_countries=Subquery(manufacturer_countries_sub_query)
    )

    applications = _add_export_certificate_data(applications)

    return applications


def get_com_applications(search_ids: list[int]) -> "QuerySet[CertificateOfManufactureApplication]":
    applications = CertificateOfManufactureApplication.objects.filter(pk__in=search_ids)
    applications = _apply_export_optimisation(applications)
    applications = _add_export_certificate_data(applications)

    return applications


def get_gmp_applications(
    search_ids: list[int],
) -> "QuerySet[CertificateOfGoodManufacturingPracticeApplication]":
    applications = CertificateOfGoodManufacturingPracticeApplication.objects.filter(
        pk__in=search_ids
    )
    applications = _apply_export_optimisation(applications)
    applications = _add_export_certificate_data(applications)

    return applications


def get_commodity_details(rec: ImportApplication) -> types.CommodityDetails:
    """Load the commodity details section"""

    app_pt = rec.process_type

    if app_pt == ProcessTypes.WOOD:
        wood_app: WoodQuotaApplication = rec

        details = types.CommodityDetails(
            origin_country="None",  # This is to match legacy for this application type
            shipping_year=wood_app.shipping_year,
            commodity_codes=[wood_app.commodity.commodity_code],
        )

    elif app_pt == ProcessTypes.FA_DFL:
        fa_dfl_app: DFLApplication = rec

        details = types.CommodityDetails(
            origin_country=fa_dfl_app.origin_country.name,
            consignment_country=fa_dfl_app.consignment_country.name,
            goods_category=fa_dfl_app.get_commodity_code_display(),
        )

    elif app_pt == ProcessTypes.FA_OIL:
        fa_oil_app: OpenIndividualLicenceApplication = rec

        details = types.CommodityDetails(
            origin_country=fa_oil_app.origin_country.name,
            consignment_country=fa_oil_app.consignment_country.name,
            goods_category=fa_oil_app.get_commodity_code_display(),
        )

    elif app_pt == ProcessTypes.FA_SIL:
        fa_sil_app: SILApplication = rec

        details = types.CommodityDetails(
            origin_country=fa_sil_app.origin_country.name,
            consignment_country=fa_sil_app.consignment_country.name,
            goods_category=fa_sil_app.get_commodity_code_display(),
        )

    elif app_pt == ProcessTypes.OPT:
        opt_app: OutwardProcessingTradeApplication = rec

        # cp_commodity_codes & teg_commodity_codes are annotations
        commodity_codes = sorted(opt_app.cp_commodity_codes + opt_app.teg_commodity_codes)

        details = types.CommodityDetails(
            origin_country=opt_app.cp_origin_country.name,
            consignment_country=opt_app.cp_processing_country.name,
            shipping_year=opt_app.submit_datetime.year,
            goods_category=opt_app.cp_category,
            commodity_codes=commodity_codes,
        )

    # TODO: Extend with NuclearMaterialApplication
    elif app_pt == ProcessTypes.SANCTIONS:
        sanction_app: SanctionsAndAdhocApplication = rec

        details = types.CommodityDetails(
            origin_country=sanction_app.origin_country.name,
            consignment_country=sanction_app.consignment_country.name,
            shipping_year=sanction_app.submit_datetime.year,
            commodity_codes=sorted(sanction_app.commodity_codes),
        )

    elif app_pt == ProcessTypes.SPS:
        sps_app: PriorSurveillanceApplication = rec

        details = types.CommodityDetails(
            origin_country=sps_app.origin_country.name,
            consignment_country=sps_app.consignment_country.name,
            shipping_year=sps_app.submit_datetime.year,
            commodity_codes=[sps_app.commodity.commodity_code],
        )

    elif app_pt == ProcessTypes.TEXTILES:
        textiles_app: TextilesApplication = rec

        details = types.CommodityDetails(
            origin_country=textiles_app.origin_country.name,
            consignment_country=textiles_app.consignment_country.name,
            goods_category=textiles_app.category_commodity_group.group_code,
            shipping_year=textiles_app.shipping_year,
            commodity_codes=[textiles_app.commodity.commodity_code],
        )

    else:
        raise NotImplementedError(f"Unsupported process type: {app_pt}")

    return details


def _apply_import_optimisation(model: "QuerySet[Model]") -> "QuerySet[Model]":
    """Selects related tables used for import applications."""
    model = model.select_related("importer", "agent", "contact", "application_type", "case_owner")
    model = model.annotate(order_by_datetime=utils.get_order_by_datetime("import"))

    return model


def _apply_export_optimisation(model: "QuerySet[Model]") -> "QuerySet[Model]":
    """Selects related tables used for import applications."""
    model = model.select_related("exporter", "agent", "contact", "case_owner")

    origin_countries_sub_query = (
        ExportApplication.objects.filter(id=OuterRef("id"))
        .order_by()
        .values("id")
        .annotate(
            origin_countries_array=ArrayAgg("countries__name", distinct=True, default=Value([]))
        )
        .values("origin_countries_array")
    )
    model = model.annotate(
        origin_countries=Subquery(origin_countries_sub_query),
        order_by_datetime=utils.get_order_by_datetime("export"),
    )

    return model


def _add_import_licence_data(model: "QuerySet[Model]", distinct: bool = True) -> "QuerySet[Model]":
    content_type_pk = get_content_type_pk("import")

    # This join will be used for all licence annotations
    # it creates a left join with extra conditions on the ON clause
    valid_licences_annotation = FilteredRelation(
        "licences",
        condition=Q(
            licences__status__in=[
                ImportApplicationLicence.Status.DRAFT,
                ImportApplicationLicence.Status.ACTIVE,
                ImportApplicationLicence.Status.REVOKED,
            ]
        ),
    )

    # Sub query that references the above "valid_licences" annotation
    sub_query = (
        CaseDocumentReference.objects.filter(
            document_type=CaseDocumentReference.Type.LICENCE,
            content_type_id=content_type_pk,
            object_id=OuterRef("valid_licences__pk"),
        )
        .order_by()
        .values("object_id")
        .annotate(
            licence_cdr_data=JSONBAgg(Func(F("pk"), F("reference"), function="json_build_array"))
        )
        .values("licence_cdr_data")
    )

    model = (
        model.annotate(
            valid_licences=valid_licences_annotation,
            latest_licence_pk=F("valid_licences__pk"),
            latest_licence_cdr_data=Subquery(sub_query.values("licence_cdr_data")),
            latest_licence_start_date=F("valid_licences__licence_start_date"),
            latest_licence_end_date=F("valid_licences__licence_end_date"),
            latest_licence_status=F("valid_licences__status"),
            latest_licence_issue_paper_licence_only=F("valid_licences__issue_paper_licence_only"),
            latest_licence_case_completion_datetime=F("valid_licences__case_completion_datetime"),
        )
        # The query generated uses `DISTINCT ON`
        # It ensures a 1 to 1 for the application and latest licence
        .order_by("id", "-valid_licences__created_at")
    )
    if distinct:
        model = model.distinct("id")
    return model


def _add_export_certificate_data(model: "QuerySet[Model]") -> "QuerySet[Model]":
    content_type_pk = get_content_type_pk("export")

    # This join will be used for all certificate annotations
    # it creates a left join with extra conditions on the ON clause
    valid_certificates_annotation = FilteredRelation(
        "certificates",
        condition=Q(
            certificates__status__in=[
                ExportApplicationCertificate.Status.DRAFT,
                ExportApplicationCertificate.Status.ACTIVE,
                ExportApplicationCertificate.Status.REVOKED,
            ]
        ),
    )

    cr_sub_query = (
        CaseDocumentReference.objects.filter(
            document_type=CaseDocumentReference.Type.CERTIFICATE,
            content_type_id=content_type_pk,
            object_id=OuterRef("valid_certificates__pk"),
        )
        .order_by()
        .values("object_id")
        .annotate(
            certificate_array=JSONBAgg(
                Func(F("pk"), F("reference"), function="json_build_array"), ordering="reference"
            )
        )
        .values("certificate_array")
    )

    model = (
        model.annotate(
            valid_certificates=valid_certificates_annotation,
            latest_certificate_pk=F("valid_certificates__pk"),
            latest_certificate_issue_datetime=F("valid_certificates__case_completion_datetime"),
            latest_certificate_references=Subquery(cr_sub_query),
        )
        # The query generated uses `DISTINCT ON`
        # It ensures a 1 to 1 for the application and latest certificate
        .order_by("id", "-valid_certificates__created_at").distinct("id")
    )

    return model


def get_content_type_pk(imp_or_exp: str) -> int:
    if imp_or_exp == "import":
        return ContentType.objects.get_for_model(ImportApplicationLicence).id
    else:
        return ContentType.objects.get_for_model(ExportApplicationCertificate).id
