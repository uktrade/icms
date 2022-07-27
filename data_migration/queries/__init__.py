from typing import Literal, Type

from django.db.models import Model

from data_migration import models as dm
from data_migration.models import task
from data_migration.utils import xml_parser
from web import models as web

from . import files, import_application, reference, user
from .types import M2M, QueryModel, SourceTarget, source_target_list

user_source_target = source_target_list(["User"])

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
    QueryModel(import_application, "ia_type", dm.ImportApplicationType),
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
    QueryModel(files, "sps_application_files", dm.FileCombined),
    QueryModel(files, "sps_docs", dm.FileCombined),
    QueryModel(files, "derogations_application_files", dm.FileCombined),
    QueryModel(files, "opt_application_files", dm.FileCombined),
    QueryModel(files, "dfl_application_files", dm.FileCombined),
    QueryModel(files, "oil_application_files", dm.FileCombined),
    QueryModel(files, "sil_application_files", dm.FileCombined),
    QueryModel(files, "sanction_application_files", dm.FileCombined),
    QueryModel(files, "wood_application_files", dm.FileCombined),
    QueryModel(files, "textiles_application_files", dm.FileCombined),
    QueryModel(files, "fa_certificate_files", dm.FileCombined),
]

ia_query_model = [
    QueryModel(user, "importers", dm.Importer),
    QueryModel(user, "offices", dm.Office),
    QueryModel(import_application, "sps_application", dm.PriorSurveillanceApplication),
    QueryModel(import_application, "derogations_application", dm.DerogationsApplication),
    QueryModel(import_application, "derogations_checklist", dm.DerogationsChecklist),
    QueryModel(import_application, "opt_application", dm.OutwardProcessingTradeApplication),
    QueryModel(import_application, "opt_checklist", dm.OPTChecklist),
    QueryModel(import_application, "fa_authorities", dm.FirearmsAuthority),
    QueryModel(import_application, "fa_authority_linked_offices", dm.FirearmsAuthorityOffice),
    QueryModel(import_application, "section5_clauses", dm.Section5Clause),
    QueryModel(import_application, "section5_authorities", dm.Section5Authority),
    QueryModel(import_application, "section5_linked_offices", dm.Section5AuthorityOffice),
    QueryModel(import_application, "sanctions_application", dm.SanctionsAndAdhocApplication),
    QueryModel(import_application, "sil_application", dm.SILApplication),
    QueryModel(import_application, "sil_checklist", dm.SILChecklist),
    QueryModel(import_application, "dfl_application", dm.DFLApplication),
    QueryModel(import_application, "dfl_checklist", dm.DFLChecklist),
    QueryModel(import_application, "oil_application", dm.OpenIndividualLicenceApplication),
    QueryModel(import_application, "oil_checklist", dm.ChecklistFirearmsOILApplication),
    QueryModel(import_application, "wood_application", dm.WoodQuotaApplication),
    QueryModel(import_application, "wood_checklist", dm.WoodQuotaChecklist),
    QueryModel(import_application, "textiles_application", dm.TextilesApplication),
    QueryModel(import_application, "textiles_checklist", dm.TextilesChecklist),
    QueryModel(import_application, "ia_licence", dm.ImportApplicationLicence),
    QueryModel(import_application, "ia_licence_docs", dm.ImportCaseDocument),
    QueryModel(import_application, "constabulary_emails", dm.CaseEmail),
]

# Possibly refactor to import process and import application by process type
ia_source_target = [
    SourceTarget(dm.Importer, web.Importer),
    SourceTarget(dm.Office, web.Office),
    SourceTarget(dm.Process, web.Process),
    SourceTarget(dm.ImportApplication, web.ImportApplication),
    SourceTarget(dm.ImportApplicationLicence, web.ImportApplicationLicence),
    SourceTarget(dm.ImportCaseDocument, web.CaseDocumentReference),
    SourceTarget(dm.CaseEmail, web.CaseEmail),
    SourceTarget(dm.ImportContact, web.ImportContact),
    SourceTarget(dm.PriorSurveillanceContractFile, web.PriorSurveillanceContractFile),
    SourceTarget(dm.PriorSurveillanceApplication, web.PriorSurveillanceApplication),
    SourceTarget(dm.DerogationsApplication, web.DerogationsApplication),
    SourceTarget(dm.DerogationsChecklist, web.DerogationsChecklist),
    SourceTarget(dm.OutwardProcessingTradeApplication, web.OutwardProcessingTradeApplication),
    SourceTarget(dm.OPTChecklist, web.OPTChecklist),
    SourceTarget(dm.OutwardProcessingTradeFile, web.OutwardProcessingTradeFile),
    SourceTarget(dm.SanctionsAndAdhocApplication, web.SanctionsAndAdhocApplication),
    SourceTarget(dm.SanctionsAndAdhocApplicationGoods, web.SanctionsAndAdhocApplicationGoods),
    SourceTarget(dm.FirearmsAuthority, web.FirearmsAuthority),
    SourceTarget(dm.FirearmsAct, web.FirearmsAct),
    SourceTarget(dm.ActQuantity, web.ActQuantity),
    SourceTarget(dm.Section5Clause, web.Section5Clause),
    SourceTarget(dm.Section5Authority, web.Section5Authority),
    SourceTarget(dm.SILUserSection5, web.SILUserSection5),
    SourceTarget(dm.ClauseQuantity, web.ClauseQuantity),
    SourceTarget(dm.SILApplication, web.SILApplication),
    SourceTarget(dm.SILChecklist, web.SILChecklist),
    SourceTarget(dm.SILGoodsSection1, web.SILGoodsSection1),
    SourceTarget(dm.SILGoodsSection2, web.SILGoodsSection2),
    SourceTarget(dm.SILGoodsSection5, web.SILGoodsSection5),
    SourceTarget(dm.SILGoodsSection582Obsolete, web.SILGoodsSection582Obsolete),  # /PS-IGNORE
    SourceTarget(dm.SILGoodsSection582Other, web.SILGoodsSection582Other),  # /PS-IGNORE
    SourceTarget(dm.SILSupplementaryInfo, web.SILSupplementaryInfo),
    SourceTarget(dm.SILSupplementaryReport, web.SILSupplementaryReport),
    SourceTarget(
        dm.SILSupplementaryReportFirearmSection1, web.SILSupplementaryReportFirearmSection1
    ),
    SourceTarget(
        dm.SILSupplementaryReportFirearmSection2, web.SILSupplementaryReportFirearmSection2
    ),
    SourceTarget(
        dm.SILSupplementaryReportFirearmSection5, web.SILSupplementaryReportFirearmSection5
    ),
    SourceTarget(
        dm.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
        web.SILSupplementaryReportFirearmSection582Obsolete,  # /PS-IGNORE
    ),
    SourceTarget(
        dm.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
        web.SILSupplementaryReportFirearmSection582Other,  # /PS-IGNORE
    ),
    SourceTarget(dm.DFLApplication, web.DFLApplication),
    SourceTarget(dm.DFLChecklist, web.DFLChecklist),
    SourceTarget(dm.DFLGoodsCertificate, web.DFLGoodsCertificate),
    SourceTarget(dm.DFLSupplementaryInfo, web.DFLSupplementaryInfo),
    SourceTarget(dm.DFLSupplementaryReport, web.DFLSupplementaryReport),
    SourceTarget(dm.DFLSupplementaryReportFirearm, web.DFLSupplementaryReportFirearm),
    SourceTarget(dm.OpenIndividualLicenceApplication, web.OpenIndividualLicenceApplication),
    SourceTarget(dm.ChecklistFirearmsOILApplication, web.ChecklistFirearmsOILApplication),
    SourceTarget(dm.OILSupplementaryInfo, web.OILSupplementaryInfo),
    SourceTarget(dm.OILSupplementaryReport, web.OILSupplementaryReport),
    SourceTarget(dm.OILSupplementaryReportFirearm, web.OILSupplementaryReportFirearm),
    SourceTarget(dm.WoodQuotaApplication, web.WoodQuotaApplication),
    SourceTarget(dm.WoodQuotaChecklist, web.WoodQuotaChecklist),
    SourceTarget(dm.WoodContractFile, web.WoodContractFile),
    SourceTarget(dm.TextilesApplication, web.TextilesApplication),
    SourceTarget(dm.TextilesChecklist, web.TextilesChecklist),
    SourceTarget(dm.UserImportCertificate, web.UserImportCertificate),
]


ia_m2m = [
    M2M(dm.VariationRequest, web.ImportApplication, "variation_requests"),
    M2M(dm.CaseEmail, web.ImportApplication, "case_emails"),
    M2M(dm.Office, web.Importer, "offices"),
    M2M(dm.FirearmsAuthorityFile, web.FirearmsAuthority, "files"),
    M2M(dm.Section5AuthorityFile, web.Section5Authority, "files"),
    M2M(dm.FirearmsAuthorityOffice, web.FirearmsAuthority, "linked_offices"),
    M2M(dm.Section5AuthorityOffice, web.Section5Authority, "linked_offices"),
    M2M(
        dm.SPSSupportingDoc,
        web.PriorSurveillanceApplication,
        "supporting_documents",
    ),
    M2M(
        dm.DerogationsSupportingDoc,
        web.DerogationsApplication,
        "supporting_documents",
    ),
    M2M(
        dm.OPTCpCommodity,
        web.OutwardProcessingTradeApplication,
        "cp_commodities",
    ),
    M2M(
        dm.OPTTegCommodity,
        web.OutwardProcessingTradeApplication,
        "teg_commodities",
    ),
    M2M(dm.OutwardProcessingTradeFile, web.OutwardProcessingTradeApplication, "documents"),
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
    M2M(
        dm.SanctionsAndAdhocSupportingDoc,
        web.SanctionsAndAdhocApplication,
        "supporting_documents",
    ),
    M2M(
        dm.TextilesSupportingDoc,
        web.TextilesApplication,
        "supporting_documents",
    ),
    M2M(
        dm.WoodContractFile,
        web.WoodQuotaApplication,
        "contract_documents",
    ),
    M2M(
        dm.WoodSupportingDoc,
        web.WoodQuotaApplication,
        "supporting_documents",
    ),
]

ia_xml = [
    xml_parser.VariationImportParser,
    xml_parser.OPTCpCommodity,
    xml_parser.OPTTegCommodity,
    xml_parser.SanctionGoodsParser,
    xml_parser.OILApplicationFirearmAuthorityParser,
    xml_parser.SILApplicationFirearmAuthorityParser,
    xml_parser.SILApplicationSection5AuthorityParser,
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
    xml_parser.WoodContractParser,
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
