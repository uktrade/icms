from typing import Literal, Type

from django.db.models import Model

from data_migration import models as dm
from data_migration.models import task
from data_migration.utils import xml_parser
from web import models as web

from . import export_application, files, import_application, reference, user
from .types import M2M, QueryModel, SourceTarget, source_target_list

user_source_target = [
    SourceTarget(dm.User, web.User),
    SourceTarget(dm.Mailshot, web.Mailshot),
    SourceTarget(dm.Importer, web.Importer),
    SourceTarget(dm.Exporter, web.Exporter),
    SourceTarget(dm.Office, web.Office),
    SourceTarget(dm.Process, web.Process),
]

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
    QueryModel(files, "gmp_files", dm.FileCombined),
    QueryModel(files, "mailshot_files", dm.FileCombined),
    QueryModel(files, "case_note_files", dm.FileCombined),
    QueryModel(files, "fir_files", dm.FileCombined),
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
    QueryModel(user, "mailshots", dm.Mailshot),
    QueryModel(user, "importers", dm.Importer),
    QueryModel(user, "importer_offices", dm.Office),
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
    QueryModel(import_application, "ia_licence_docs", dm.CaseDocument),
    QueryModel(import_application, "constabulary_emails", dm.CaseEmail),
    QueryModel(import_application, "case_note", dm.CaseNote),
    QueryModel(import_application, "update_request", dm.UpdateRequest),
    QueryModel(import_application, "fir", dm.FurtherInformationRequest),
    QueryModel(import_application, "endorsement", dm.EndorsementImportApplication),
]

ia_source_target = [
    SourceTarget(dm.ImportApplication, web.ImportApplication),
    SourceTarget(dm.ImportApplicationLicence, web.ImportApplicationLicence),
    SourceTarget(dm.ImportCaseDocument, web.CaseDocumentReference),
    SourceTarget(dm.CaseEmail, web.CaseEmail),
    SourceTarget(dm.CaseNote, web.CaseNote),
    SourceTarget(dm.UpdateRequest, web.UpdateRequest),
    SourceTarget(dm.FurtherInformationRequest, web.FurtherInformationRequest),
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
    SourceTarget(dm.EndorsementImportApplication, web.EndorsementImportApplication),
]


ia_m2m = [
    M2M(dm.MailshotDoc, web.Mailshot, "documents"),
    M2M(dm.VariationRequest, web.ImportApplication, "variation_requests"),
    M2M(dm.CaseEmail, web.ImportApplication, "case_emails"),
    M2M(dm.CaseNote, web.ImportApplication, "case_notes"),
    M2M(dm.UpdateRequest, web.ImportApplication, "update_requests"),
    M2M(dm.FurtherInformationRequest, web.ImportApplication, "further_information_requests"),
    M2M(dm.FIRFile, web.FurtherInformationRequest, "files"),
    M2M(dm.CaseNoteFile, web.CaseNote, "files"),
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

export_query_model = [
    QueryModel(user, "exporters", dm.Exporter),
    QueryModel(user, "exporter_offices", dm.Office),
    QueryModel(export_application, "product_legislation", dm.ProductLegislation),
    QueryModel(export_application, "export_application_type", dm.ExportApplicationType),
    QueryModel(export_application, "com_application", dm.CertificateOfManufactureApplication),
    QueryModel(
        export_application, "gmp_application", dm.CertificateOfGoodManufacturingPracticeApplication
    ),
    QueryModel(export_application, "cfs_application", dm.CertificateOfFreeSaleApplication),
    QueryModel(export_application, "cfs_schedule", dm.CFSSchedule),
    QueryModel(export_application, "export_application_countries", dm.ExportApplicationCountries),
    QueryModel(export_application, "export_certificate", dm.ExportApplicationCertificate),
    QueryModel(
        export_application, "export_certificate_docs", dm.ExportCertificateCaseDocumentReferenceData
    ),
]

export_source_target = [
    SourceTarget(dm.ProductLegislation, web.ProductLegislation),
    SourceTarget(dm.ExportApplicationType, web.ExportApplicationType),
    SourceTarget(dm.ExportApplication, web.ExportApplication),
    SourceTarget(dm.CertificateOfManufactureApplication, web.CertificateOfManufactureApplication),
    SourceTarget(
        dm.CertificateOfGoodManufacturingPracticeApplication,
        web.CertificateOfGoodManufacturingPracticeApplication,
    ),
    SourceTarget(dm.GMPFile, web.GMPFile),
    SourceTarget(dm.GMPBrand, web.GMPBrand),
    SourceTarget(dm.CertificateOfFreeSaleApplication, web.CertificateOfFreeSaleApplication),
    SourceTarget(dm.CFSSchedule, web.CFSSchedule),
    SourceTarget(dm.CFSProduct, web.CFSProduct),
    SourceTarget(dm.CFSProductType, web.CFSProductType),
    SourceTarget(dm.CFSProductActiveIngredient, web.CFSProductActiveIngredient),
    SourceTarget(dm.ExportApplicationCertificate, web.ExportApplicationCertificate),
    SourceTarget(dm.ExportCaseDocument, web.CaseDocumentReference),
    SourceTarget(
        dm.ExportCertificateCaseDocumentReferenceData,
        web.ExportCertificateCaseDocumentReferenceData,
    ),
]

export_m2m = [
    M2M(dm.Office, web.Exporter, "offices"),
    M2M(dm.ExportApplicationCountries, web.ExportApplication, "countries"),
    M2M(dm.GMPFile, web.CertificateOfGoodManufacturingPracticeApplication, "supporting_documents"),
    M2M(dm.CFSLegislation, web.CFSSchedule, "legislations"),
]

export_xml = [
    xml_parser.CFSLegislationParser,
    xml_parser.CFSProductParser,
    xml_parser.ProductTypeParser,
    xml_parser.ActiveIngredientParser,
]


DATA_TYPE = Literal["reference", "import_application", "user", "file", "export_application"]

DATA_TYPE_QUERY_MODEL: dict[str, list[QueryModel]] = {
    "export_application": export_query_model,
    "file": file_query_model,
    "import_application": ia_query_model,
    "reference": ref_query_model,
}

DATA_TYPE_SOURCE_TARGET: dict[str, list[SourceTarget]] = {
    "export_application": export_source_target,
    "file": source_target_list(["File"]),
    "import_application": ia_source_target,
    "reference": ref_source_target,
    "user": user_source_target,
}

DATA_TYPE_M2M: dict[str, list[M2M]] = {
    "export_application": export_m2m,
    "import_application": ia_m2m,
    "reference": ref_m2m,
    "user": [],
}

DATA_TYPE_XML: dict[str, list[Type[xml_parser.BaseXmlParser]]] = {
    "export_application": export_xml,
    "import_application": ia_xml,
    "reference": [],
    "user": [],
}

TASK_LIST = [
    task.PrepareTask,
    task.ProcessTask,
]

FILE_MODELS: list[Type[Model]] = [dm.FileFolder, dm.FileTarget, dm.File]
