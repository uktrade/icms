from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands._types import M2M, QueryModel, SourceTarget
from data_migration.utils import xml_parser
from web import models as web

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
    QueryModel(queries.constabulary_emails, "constabulary_emails", dm.CaseEmail),
    QueryModel(queries.case_note, "case_note", dm.CaseNote),
    QueryModel(queries.update_request, "update_request", dm.UpdateRequest),
    QueryModel(queries.fir, "fir", dm.FurtherInformationRequest),
    QueryModel(queries.endorsement, "endorsement", dm.EndorsementImportApplication),
    QueryModel(queries.sigl_transmission, "sigl_transmission", dm.SIGLTransmission),
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
