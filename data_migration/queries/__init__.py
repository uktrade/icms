from types import ModuleType
from typing import Literal, NamedTuple, Type

from django.db.models import Model

from data_migration import models as dm
from data_migration.models import task
from data_migration.utils import xml_parser
from web import models as web

from . import files, import_application, reference

QueryModel = NamedTuple("QueryModel", [("module", ModuleType), ("query", str), ("model", Model)])
SourceTarget = NamedTuple("SourceTarget", [("source", Model), ("target", Model)])
M2M = NamedTuple("M2M", [("source", Model), ("target", Model), ("field", str)])


def source_target_list(lst: list[str]):
    return [SourceTarget(getattr(dm, model_name), getattr(web, model_name)) for model_name in lst]


user_source_target = source_target_list(["User", "Importer", "Office"])

ref_query_model = [
    QueryModel(reference, "country", dm.Country),
    QueryModel(reference, "country_group", dm.CountryGroup),
    QueryModel(reference, "country_group_country", dm.CountryGroupCountry),
    QueryModel(reference, "country_translation_set", dm.CountryTranslationSet),
    QueryModel(reference, "country_translation", dm.CountryTranslation),
    QueryModel(reference, "unit", dm.Unit),
    QueryModel(reference, "commodity_type", dm.CommodityType),
    QueryModel(reference, "commodity_group", dm.CommodityGroup),
    QueryModel(reference, "commodity", dm.Commodity),
    QueryModel(reference, "commodity_group_commodity", dm.CommodityGroupCommodity),
    QueryModel(import_application, "import_application_type", dm.ImportApplicationType),
    QueryModel(import_application, "usage", dm.Usage),
    QueryModel(reference, "constabularies", dm.Constabulary),
    QueryModel(reference, "obsolete_calibre_group", dm.ObsoleteCalibreGroup),
    QueryModel(reference, "obsolete_calibre", dm.ObsoleteCalibre),
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
        "ObsoleteCalibreGroup",
        "ObsoleteCalibre",
    ]
)

ref_m2m = [
    M2M(dm.CountryGroupCountry, web.CountryGroup, "countries"),
    M2M(dm.CommodityGroupCommodity, web.CommodityGroup, "commodities"),
]

file_query_model = [
    QueryModel(files, "dfl_application_files", dm.FileCombined),
    QueryModel(files, "oil_application_files", dm.FileCombined),
    QueryModel(files, "sil_application_files", dm.FileCombined),
    QueryModel(files, "sanction_application_files", dm.FileCombined),
    QueryModel(files, "wood_application_files", dm.FileCombined),
    QueryModel(files, "textiles_application_files", dm.FileCombined),
    QueryModel(files, "fa_certificate_files", dm.FileCombined),
]

ia_query_model = [
    QueryModel(import_application, "fa_authorities", dm.FirearmsAuthority),
    # QueryModel(import_application, "fa_authority_linked_offices", dm.FirearmsAuthorityOffice),
    QueryModel(import_application, "section5_clauses", dm.Section5Clause),
    QueryModel(import_application, "section5_authorities", dm.Section5Authority),
    # QueryModel(import_application, "section5_linked_offices", dm.Section5AuthorityOffice),
    QueryModel(import_application, "sanctions_application", dm.SanctionsAndAdhocApplication),
    QueryModel(import_application, "sil_application", dm.SILApplication),
    QueryModel(import_application, "dfl_application", dm.DFLApplication),
    QueryModel(import_application, "oil_application", dm.OpenIndividualLicenceApplication),
    QueryModel(import_application, "wood_application", dm.WoodQuotaApplication),
    # QueryModel(import_application, "wood_checklist", dm.WoodQuotaChecklist),  TODO ICMSLST-1510
    QueryModel(import_application, "textiles_application", dm.TextilesApplication),
    # QueryModel(import_application, "textiles_checklist", dm.TextilesChecklist), TODO ICMSLST-1510
    QueryModel(import_application, "import_application_licence", dm.ImportApplicationLicence),
]

# Possibly refactor to import process and import application by process type
ia_source_target = source_target_list(
    [
        "Process",
        "ImportApplication",
        "ImportContact",
        "SanctionsAndAdhocApplication",
        "SanctionsAndAdhocApplicationGoods",
        "FirearmsAuthority",
        "FirearmsAct",
        "ActQuantity",
        "Section5Clause",
        "Section5Authority",
        "SILUserSection5",
        "ClauseQuantity",
        "SILApplication",
        "SILGoodsSection1",
        "SILGoodsSection2",
        "SILGoodsSection5",
        "SILGoodsSection582Obsolete",  # /PS-IGNORE
        "SILGoodsSection582Other",  # /PS-IGNORE
        "SILSupplementaryInfo",
        "SILSupplementaryReport",
        "SILSupplementaryReportFirearmSection1",
        "SILSupplementaryReportFirearmSection2",
        "SILSupplementaryReportFirearmSection5",
        "SILSupplementaryReportFirearmSection582Obsolete",  # /PS-IGNORE
        "SILSupplementaryReportFirearmSection582Other",  # /PS-IGNORE
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
        dm.OILApplicationFirearmAuthority,
        web.OpenIndividualLicenceApplication,
        "verified_certificates",
    ),
    M2M(
        dm.SILApplicationFirearmAuthority,
        web.SILApplication,
        "verified_certificates",
    ),
    M2M(
        dm.SILApplicationSection5Authority,
        web.SILApplication,
        "verified_section5",
    ),
    M2M(dm.SILUserSection5, web.SILApplication, "user_section5"),
    # TODO Section5 and auth linked offices
    M2M(
        dm.UserImportCertificate,
        web.SILApplication,
        "user_imported_certificates",
    ),
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
    xml_parser.SanctionGoodsParser,
    xml_parser.OILApplicationFirearmAuthorityParser,
    xml_parser.SILApplicationFirearmAuthorityParser,
    xml_parser.SILApplicationSection5AuthorityParser,
    xml_parser.FirearmsAuthorityFileParser,
    xml_parser.Section5AuthorityFileParser,
    xml_parser.ClauseQuantityParser,
    xml_parser.ImportContactParser,
    xml_parser.UserImportCertificateParser,
    xml_parser.SILGoodsParser,
    xml_parser.SILSupplementaryReportParser,
    xml_parser.SILReportFirearmParser,
    xml_parser.DFLGoodsCertificateParser,
    xml_parser.DFLSupplementaryReportParser,
    xml_parser.DFLReportFirearmParser,
    xml_parser.OILSupplementaryReportParser,
    xml_parser.OILReportFirearmParser,
]

DATA_TYPE = Literal["reference", "import_application", "user", "file"]

DATA_TYPE_QUERY_MODEL: dict[str, list[QueryModel]] = {
    "reference": ref_query_model,
    "import_application": ia_query_model,
    "file": file_query_model,
}

DATA_TYPE_SOURCE_TARGET: dict[str, list[SourceTarget]] = {
    "user": user_source_target,
    "reference": ref_source_target,
    "import_application": ia_source_target,
    "file": source_target_list(["File"]),
}

DATA_TYPE_M2M: dict[str, list[M2M]] = {
    "user": [],
    "reference": ref_m2m,
    "import_application": ia_m2m,
}

DATA_TYPE_XML: dict[str, list[Type[xml_parser.BaseXmlParser]]] = {
    "user": [],
    "reference": [],
    "import_application": ia_xml,
}

TASK_LIST = [
    task.PrepareTask,
    task.ProcessTask,
]

FILE_MODELS: list[Type[Model]] = [dm.FileFolder, dm.FileTarget, dm.File]
