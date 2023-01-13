from typing import Literal

from django.db.models import Model

from data_migration import models as dm
from data_migration import queries
from data_migration.models import task
from data_migration.models.import_application.import_application import SIGLTransmission
from data_migration.utils import xml_parser
from web import models as web

from ._types import M2M, QueryModel, SourceTarget, source_target_list

user_source_target = [
    SourceTarget(dm.User, web.User),
    SourceTarget(dm.PersonalEmail, web.PersonalEmail),
    SourceTarget(dm.AlternativeEmail, web.AlternativeEmail),
    SourceTarget(dm.PhoneNumber, web.PhoneNumber),
    SourceTarget(dm.Mailshot, web.Mailshot),
    SourceTarget(dm.Importer, web.Importer),
    SourceTarget(dm.Exporter, web.Exporter),
    SourceTarget(dm.Office, web.Office),
    SourceTarget(dm.Process, web.Process),
    SourceTarget(dm.FurtherInformationRequest, web.FurtherInformationRequest),
    SourceTarget(dm.AccessRequest, web.AccessRequest),
    SourceTarget(dm.ImporterAccessRequest, web.ImporterAccessRequest),
    SourceTarget(dm.ExporterAccessRequest, web.ExporterAccessRequest),
    SourceTarget(dm.ApprovalRequest, web.ApprovalRequest),
    SourceTarget(dm.ImporterApprovalRequest, web.ImporterApprovalRequest),
    SourceTarget(dm.ExporterApprovalRequest, web.ExporterApprovalRequest),
]

user_query_model = [
    QueryModel(queries.users, "users", dm.User),
    QueryModel(queries.importers, "importers", dm.Importer),
    QueryModel(queries.importer_offices, "importer_offices", dm.Office),
    QueryModel(queries.exporters, "exporters", dm.Exporter),
    QueryModel(queries.exporter_offices, "exporter_offices", dm.Office),
    QueryModel(queries.access_requests, "access_requests", dm.AccessRequest),
]

user_m2m = [
    M2M(dm.Office, web.Importer, "offices"),
    M2M(dm.Office, web.Exporter, "offices"),
    M2M(dm.FurtherInformationRequest, web.AccessRequest, "further_information_requests"),
]

user_xml = [
    xml_parser.PhoneNumberParser,
    xml_parser.EmailAddressParser,
    xml_parser.ApprovalRequestParser,
    xml_parser.AccessFIRParser,
]

ref_query_model = [
    QueryModel(queries.country, "country", dm.Country),
    QueryModel(queries.country_group, "country_group", dm.CountryGroup),
    QueryModel(queries.country_group_country, "country_group_country", dm.CountryGroupCountry),
    QueryModel(
        queries.country_translation_set, "country_translation_set", dm.CountryTranslationSet
    ),
    QueryModel(queries.country_translation, "country_translation", dm.CountryTranslation),
    QueryModel(queries.unit, "unit", dm.Unit),
    QueryModel(queries.commodity_type, "commodity_type", dm.CommodityType),
    QueryModel(queries.commodity_group, "commodity_group", dm.CommodityGroup),
    QueryModel(queries.commodity, "commodity", dm.Commodity),
    QueryModel(
        queries.commodity_group_commodity, "commodity_group_commodity", dm.CommodityGroupCommodity
    ),
    QueryModel(queries.ia_type, "ia_type", dm.ImportApplicationType),
    QueryModel(queries.usage, "usage", dm.Usage),
    QueryModel(queries.constabularies, "constabularies", dm.Constabulary),
    QueryModel(queries.obsolete_calibre_group, "obsolete_calibre_group", dm.ObsoleteCalibreGroup),
    QueryModel(queries.obsolete_calibre, "obsolete_calibre", dm.ObsoleteCalibre),
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
        "CaseNote",
        "CaseEmail",
        "UpdateRequest",
    ]
)

ref_m2m = [
    M2M(dm.CountryGroupCountry, web.CountryGroup, "countries"),
    M2M(dm.CommodityGroupCommodity, web.CommodityGroup, "commodities"),
]

file_query_model = [
    QueryModel(queries.gmp_files, "gmp_files", dm.FileCombined),
    QueryModel(queries.mailshot_files, "mailshot_files", dm.FileCombined),
    QueryModel(queries.case_note_files, "case_note_files", dm.FileCombined),
    QueryModel(queries.fir_files, "fir_files", dm.FileCombined),
    QueryModel(queries.sps_application_files, "sps_application_files", dm.FileCombined),
    QueryModel(queries.sps_docs, "sps_docs", dm.FileCombined),
    QueryModel(
        queries.derogations_application_files, "derogations_application_files", dm.FileCombined
    ),
    QueryModel(queries.opt_application_files, "opt_application_files", dm.FileCombined),
    QueryModel(queries.dfl_application_files, "dfl_application_files", dm.FileCombined),
    QueryModel(queries.oil_application_files, "oil_application_files", dm.FileCombined),
    QueryModel(queries.sil_application_files, "sil_application_files", dm.FileCombined),
    QueryModel(queries.sanction_application_files, "sanction_application_files", dm.FileCombined),
    QueryModel(queries.wood_application_files, "wood_application_files", dm.FileCombined),
    QueryModel(queries.textiles_application_files, "textiles_application_files", dm.FileCombined),
    QueryModel(queries.fa_certificate_files, "fa_certificate_files", dm.FileCombined),
    QueryModel(queries.export_case_note_docs, "export_case_note_docs", dm.FileCombined),
]

ia_query_model = [
    QueryModel(queries.sps_application, "sps_application", dm.PriorSurveillanceApplication),
    QueryModel(
        queries.derogations_application, "derogations_application", dm.DerogationsApplication
    ),
    QueryModel(queries.derogations_checklist, "derogations_checklist", dm.DerogationsChecklist),
    QueryModel(queries.opt_application, "opt_application", dm.OutwardProcessingTradeApplication),
    QueryModel(queries.opt_checklist, "opt_checklist", dm.OPTChecklist),
    QueryModel(queries.fa_authorities, "fa_authorities", dm.FirearmsAuthority),
    QueryModel(
        queries.fa_authority_linked_offices,
        "fa_authority_linked_offices",
        dm.FirearmsAuthorityOffice,
    ),
    QueryModel(queries.section5_clauses, "section5_clauses", dm.Section5Clause),
    QueryModel(queries.section5_authorities, "section5_authorities", dm.Section5Authority),
    QueryModel(
        queries.section5_linked_offices, "section5_linked_offices", dm.Section5AuthorityOffice
    ),
    QueryModel(
        queries.sanctions_application, "sanctions_application", dm.SanctionsAndAdhocApplication
    ),
    QueryModel(queries.sil_application, "sil_application", dm.SILApplication),
    QueryModel(queries.sil_checklist, "sil_checklist", dm.SILChecklist),
    QueryModel(queries.dfl_application, "dfl_application", dm.DFLApplication),
    QueryModel(queries.dfl_checklist, "dfl_checklist", dm.DFLChecklist),
    QueryModel(queries.oil_application, "oil_application", dm.OpenIndividualLicenceApplication),
    QueryModel(queries.oil_checklist, "oil_checklist", dm.ChecklistFirearmsOILApplication),
    QueryModel(queries.wood_application, "wood_application", dm.WoodQuotaApplication),
    QueryModel(queries.wood_checklist, "wood_checklist", dm.WoodQuotaChecklist),
    QueryModel(queries.textiles_application, "textiles_application", dm.TextilesApplication),
    QueryModel(queries.textiles_checklist, "textiles_checklist", dm.TextilesChecklist),
    QueryModel(queries.ia_licence, "ia_licence", dm.ImportApplicationLicence),
    QueryModel(queries.ia_licence_docs, "ia_licence_docs", dm.CaseDocument),
    QueryModel(queries.constabulary_emails, "constabulary_emails", dm.CaseEmail),
    QueryModel(queries.case_note, "case_note", dm.CaseNote),
    QueryModel(queries.update_request, "update_request", dm.UpdateRequest),
    QueryModel(queries.fir, "fir", dm.FurtherInformationRequest),
    QueryModel(queries.endorsement, "endorsement", dm.EndorsementImportApplication),
    QueryModel(queries.sigl_transmission, "sigl_transmission", SIGLTransmission),
    QueryModel(queries.mailshots, "mailshots", dm.Mailshot),
]

ia_source_target = [
    SourceTarget(dm.ImportApplication, web.ImportApplication),
    SourceTarget(dm.ImportApplicationLicence, web.ImportApplicationLicence),
    SourceTarget(dm.ImportCaseDocument, web.CaseDocumentReference),
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
    SourceTarget(dm.SILLegacyGoods, web.SILLegacyGoods),  # /PS-IGNORE
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
    SourceTarget(
        dm.SILSupplementaryReportFirearmSectionLegacy,
        web.SILSupplementaryReportFirearmSectionLegacy,
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
    SourceTarget(dm.VariationRequest, web.VariationRequest),
    SourceTarget(dm.SIGLTransmission, web.SIGLTransmission),
]


ia_m2m = [
    M2M(dm.MailshotDoc, web.Mailshot, "documents"),
    M2M(dm.SIGLTransmission, web.ImportApplication, "sigl_transmissions"),
    M2M(dm.VariationRequest, web.ImportApplication, "variation_requests"),
    M2M(dm.CaseEmail, web.ImportApplication, "case_emails"),
    M2M(dm.CaseNote, web.ImportApplication, "case_notes"),
    M2M(dm.UpdateRequest, web.ImportApplication, "update_requests"),
    M2M(dm.FurtherInformationRequest, web.ImportApplication, "further_information_requests"),
    M2M(dm.FIRFile, web.FurtherInformationRequest, "files"),
    M2M(dm.CaseNoteFile, web.CaseNote, "files"),
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
    xml_parser.ActQuantityParser,
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
    QueryModel(queries.product_legislation, "product_legislation", dm.ProductLegislation),
    QueryModel(
        queries.export_application_type, "export_application_type", dm.ExportApplicationType
    ),
    QueryModel(queries.com_application, "com_application", dm.CertificateOfManufactureApplication),
    QueryModel(
        queries.gmp_application,
        "gmp_application",
        dm.CertificateOfGoodManufacturingPracticeApplication,
    ),
    QueryModel(queries.cfs_application, "cfs_application", dm.CertificateOfFreeSaleApplication),
    QueryModel(queries.cfs_schedule, "cfs_schedule", dm.CFSSchedule),
    QueryModel(
        queries.export_application_countries,
        "export_application_countries",
        dm.ExportApplicationCountries,
    ),
    QueryModel(queries.export_certificate, "export_certificate", dm.ExportApplicationCertificate),
    QueryModel(
        queries.export_certificate_docs,
        "export_certificate_docs",
        dm.ExportCertificateCaseDocumentReferenceData,
    ),
    QueryModel(queries.beis_emails, "beis_emails", dm.CaseEmail),
    QueryModel(queries.hse_emails, "hse_emails", dm.CaseEmail),
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
    M2M(dm.VariationRequest, web.ExportApplication, "variation_requests"),
    M2M(dm.ExportApplicationCountries, web.ExportApplication, "countries"),
    M2M(dm.GMPFile, web.CertificateOfGoodManufacturingPracticeApplication, "supporting_documents"),
    M2M(dm.CFSLegislation, web.CFSSchedule, "legislations"),
    M2M(dm.CaseNote, web.ExportApplication, "case_notes"),
    M2M(dm.CaseEmail, web.ExportApplication, "case_emails"),
    M2M(dm.FurtherInformationRequest, web.ExportApplication, "further_information_requests"),
    M2M(dm.UpdateRequest, web.ExportApplication, "update_requests"),
]

export_xml = [
    xml_parser.CFSLegislationParser,
    xml_parser.CFSProductParser,
    xml_parser.ProductTypeParser,
    xml_parser.ActiveIngredientParser,
    xml_parser.CaseNoteExportParser,
    xml_parser.FIRExportParser,
    xml_parser.UpdateExportParser,
    xml_parser.VariationExportParser,
]


DATA_TYPE = Literal["reference", "import_application", "user", "file", "export_application"]

DATA_TYPE_QUERY_MODEL: dict[str, list[QueryModel]] = {
    "export_application": export_query_model,
    "file": file_query_model,
    "import_application": ia_query_model,
    "reference": ref_query_model,
    "user": user_query_model,
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
    "user": user_m2m,
}

DATA_TYPE_XML: dict[str, list[type[xml_parser.BaseXmlParser]]] = {
    "export_application": export_xml,
    "import_application": ia_xml,
    "reference": [],
    "user": user_xml,
}

TASK_LIST = [
    task.PrepareTask,
    task.ProcessTask,
]

FILE_MODELS: list[type[Model]] = [dm.FileFolder, dm.FileTarget, dm.DocFolder, dm.File]


TIMESTAMP_UPDATES: list[type[Model]] = [
    dm.ApprovalRequest,
    dm.CFSSchedule,
    dm.CaseNote,
    dm.Commodity,
    dm.CommodityGroup,
    dm.ExportApplicationCertificate,
    dm.File,
    dm.FurtherInformationRequest,
    dm.ImportApplication,
    dm.ImportApplicationLicence,
    dm.ImportContact,
    dm.Mailshot,
    dm.Process,
    dm.Section5Clause,
    dm.VariationRequest,
]

# TODO ICMSLST-1832 EndorsementImportApplication - check if needed in V2
# TODO ICMSLST-1832 WithdrawApplication
# TODO ICMSLST-1833 CertificateApplicationTemplate
# TODO ICMLST-1834 Template
