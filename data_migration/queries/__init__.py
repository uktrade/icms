from typing import Literal, NamedTuple

from django.db.models import Model

from data_migration import models as dm
from data_migration.models import task
from web import models as web

from . import import_application, reference

QueryModel = NamedTuple("QueryModel", [("query", str), ("model", Model)])
SourceTarget = NamedTuple("SourceTarget", [("source", Model), ("target", Model)])
M2M = NamedTuple("M2M", [("source", Model), ("target", Model), ("field", str)])
XML = NamedTuple("XML", [("parent", Model), ("field", str), ("child", Model)])


def source_target_list(lst: list[str]):
    return [SourceTarget(getattr(dm, model_name), getattr(web, model_name)) for model_name in lst]


user_source_target = source_target_list(["User", "Importer", "Office"])

ref_query_model = [
    QueryModel(reference.country, dm.Country),
    QueryModel(reference.country_group, dm.CountryGroup),
    QueryModel(reference.country_group_country, dm.CountryGroupCountry),
    QueryModel(reference.country_translation_set, dm.CountryTranslationSet),
    QueryModel(reference.country_translation, dm.CountryTranslation),
    QueryModel(reference.unit, dm.Unit),
    QueryModel(reference.commodity_type, dm.CommodityType),
    QueryModel(reference.commodity_group, dm.CommodityGroup),
    QueryModel(reference.commodity, dm.Commodity),
    QueryModel(reference.commodity_group_commodity, dm.CommodityGroupCommodity),
    QueryModel(import_application.import_application_type, dm.ImportApplicationType),
    QueryModel(import_application.usage, dm.Usage),
    QueryModel(reference.constabularies, dm.Constabulary),
]

ref_source_target = source_target_list(
    [
        "Country",
        "CountryGroup",
        "CountryTranslationSet",
        "CountryTranslation",
        "Unit",
        "CommodityType",
        "CommodityGroup",
        "Commodity",
        "ImportApplicationType",
        "Usage",
        "Constabulary",
    ]
)

ref_m2m = [
    M2M(dm.CountryGroupCountry, web.CountryGroup, "countries"),
    M2M(dm.CommodityGroupCommodity, web.CommodityGroup, "commodities"),
]

ia_query_model = [
    QueryModel(import_application.fa_file_target, dm.FileTarget),
    QueryModel(import_application.fa_certificates, dm.File),
    QueryModel(import_application.dfl_application, dm.DFLApplication),
    QueryModel(import_application.oil_application, dm.OpenIndividualLicenceApplication),
    QueryModel(import_application.wood_application, dm.WoodQuotaApplication),
    # QueryModel(import_application.wood_checklist, dm.WoodQuotaChecklist),  TODO ICMSLST-1510
    QueryModel(import_application.textiles_application, dm.TextilesApplication),
    # QueryModel(import_application.textiles_checklist, dm.TextilesChecklist), TODO ICMSLST-1510
    QueryModel(import_application.import_application_licence, dm.ImportApplicationLicence),
]

# Possibly refactor to import process and import application by process type
ia_source_target = source_target_list(
    [
        "File",
        "Process",
        "ImportApplication",
        "ImportContact",
        "DFLApplication",
        "DFLGoodsCertificate",
        "DFLSupplementaryInfo",
        "DFLSupplementaryReport",
        "DFLSupplementaryReportFirearm",
        "OpenIndividualLicenceApplication",
        "OILSupplementaryInfo",
        "OILSupplementaryReport",
        "OILSupplementaryReportFirearm",
        "WoodQuotaApplication",
        # "WoodQuotaChecklist", TODO ICMSLST-1510
        "TextilesApplication",
        # "TextilesChecklist", TODO ICMSLST-1510
        "ImportApplicationLicence",
        "UserImportCertificate",
    ]
)

ia_m2m = [
    M2M(
        dm.DFLGoodsCertificate,
        web.DFLApplication,
        "goods_certificates",
    ),
    M2M(
        dm.UserImportCertificate,
        web.OpenIndividualLicenceApplication,
        "user_imported_certificates",
    ),
]

ia_xml = [
    XML(dm.DFLApplication, "bought_from_details_xml", dm.ImportContact),
    XML(dm.DFLApplication, "fa_goods_certs_xml", dm.DFLGoodsCertificate),
    XML(dm.OpenIndividualLicenceApplication, "bought_from_details_xml", dm.ImportContact),
    XML(dm.OpenIndividualLicenceApplication, "fa_certs_xml", dm.UserImportCertificate),
    XML(dm.OILSupplementaryInfo, "supplementary_report_xml", dm.OILSupplementaryReport),
    XML(
        dm.OILSupplementaryReport,
        "report_firearms_xml",
        dm.OILSupplementaryReportFirearm,
    ),
]

DATA_TYPE = Literal["reference", "import_application", "user"]

DATA_TYPE_QUERY_MODEL: dict[str, list[QueryModel]] = {
    "reference": ref_query_model,
    "import_application": ia_query_model,
}

DATA_TYPE_SOURCE_TARGET: dict[str, list[SourceTarget]] = {
    "user": user_source_target,
    "reference": ref_source_target,
    "import_application": ia_source_target,
}

DATA_TYPE_M2M: dict[str, list[M2M]] = {
    "user": [],
    "reference": ref_m2m,
    "import_application": ia_m2m,
}

DATA_TYPE_XML: dict[str, list[XML]] = {
    "user": [],
    "reference": [],
    "import_application": ia_xml,
}

TASK_LIST = [
    task.PrepareTask,
    task.ProcessTask,
]
