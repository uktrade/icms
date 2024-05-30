from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands.types import M2M, QueryModel, SourceTarget
from web import models as web

DEFAULT_FILE_CREATED_DATETIME = "2013-01-01 01:00:00"
DEFAULT_SECURE_LOB_REF_ID = 0

file_folder_query_model = [
    QueryModel(
        queries.import_application_folders,
        "SPS Application File Folders",
        dm.FileFolder,
        {
            "ima_type": "SPS",
            "ima_sub_type": "SPS1",
            "app_model": "priorsurveillanceapplication",
        },
    ),
    QueryModel(
        queries.import_application_file_targets,
        "SPS Application File Targets",
        dm.FileTarget,
        {
            "ima_type": "SPS",
            "ima_sub_type": "SPS1",
        },
    ),
    QueryModel(
        queries.import_application_folders,
        "FA-DFL Application File Folders",
        dm.FileFolder,
        {
            "ima_type": "FA",
            "ima_sub_type": "DEACTIVATED",
            "app_model": "dflapplication",
        },
    ),
    QueryModel(
        queries.import_application_file_targets,
        "FA-DFL Application File Targets",
        dm.FileTarget,
        {
            "ima_type": "FA",
            "ima_sub_type": "DEACTIVATED",
        },
    ),
    QueryModel(
        queries.import_application_folders,
        "FA-OIL Application File Folders",
        dm.FileFolder,
        {
            "ima_type": "FA",
            "ima_sub_type": "OIL",
            "app_model": "openindividuallicenceapplication",
        },
    ),
    QueryModel(
        queries.import_application_file_targets,
        "FA-OIL Application File Targets",
        dm.FileTarget,
        {
            "ima_type": "FA",
            "ima_sub_type": "OIL",
        },
    ),
    QueryModel(
        queries.import_application_folders,
        "FA-SIL Application File Folders",
        dm.FileFolder,
        {
            "ima_type": "FA",
            "ima_sub_type": "SIL",
            "app_model": "silapplication",
        },
    ),
    QueryModel(
        queries.import_application_file_targets,
        "FA-SIL Application File Targets",
        dm.FileTarget,
        {
            "ima_type": "FA",
            "ima_sub_type": "SIL",
        },
    ),
    QueryModel(
        queries.import_application_folders,
        "Sanctions & Adhoc Application File Folders",
        dm.FileFolder,
        {
            "ima_type": "ADHOC",
            "ima_sub_type": "ADHOC1",
            "app_model": "sanctionsandadhocapplication",
        },
    ),
    QueryModel(
        queries.import_application_file_targets,
        "Sanctions & Adhoc Application File Targets",
        dm.FileTarget,
        {
            "ima_type": "ADHOC",
            "ima_sub_type": "ADHOC1",
        },
    ),
    QueryModel(
        queries.import_application_folders,
        "OPT Application File Folders",
        dm.FileFolder,
        {
            "ima_type": "OPT",
            "ima_sub_type": "QUOTA",
            "app_model": "outwardprocessingtradeapplication",
        },
    ),
    QueryModel(
        queries.import_application_file_targets,
        "OPT Application File Targets",
        dm.FileTarget,
        {
            "ima_type": "OPT",
            "ima_sub_type": "QUOTA",
        },
    ),
    QueryModel(
        queries.import_application_folders,
        "Textiles Application File Folders",
        dm.FileFolder,
        {
            "ima_type": "TEX",
            "ima_sub_type": "QUOTA",
            "app_model": "textilesapplication",
        },
    ),
    QueryModel(
        queries.import_application_file_targets,
        "Textiles Application File Targets",
        dm.FileTarget,
        {
            "ima_type": "TEX",
            "ima_sub_type": "QUOTA",
        },
    ),
    QueryModel(
        queries.import_application_folders,
        "Wood Application File Folders",
        dm.FileFolder,
        {
            "ima_type": "WD",
            "ima_sub_type": "QUOTA",
            "app_model": "woodquotaapplication",
        },
    ),
    QueryModel(
        queries.import_application_file_targets,
        "Wood Application File Targets",
        dm.FileTarget,
        {
            "ima_type": "WD",
            "ima_sub_type": "QUOTA",
        },
    ),
    QueryModel(
        queries.fa_certificate_folders,
        "Firearms & Ammunition Certificate File Folders",
        dm.FileFolder,
    ),
    QueryModel(
        queries.fa_certificate_file_targets,
        "Firearms & Ammunition Certificate File Targets",
        dm.FileTarget,
    ),
    QueryModel(
        queries.fir_file_folders,
        "Further Information Request File Folders",
        dm.FileFolder,
    ),
    QueryModel(
        queries.fir_file_targets,
        "Further Information Request File Targets",
        dm.FileTarget,
    ),
    QueryModel(
        queries.mailshot_file_folders,
        "Mailshot File Folders",
        dm.FileFolder,
    ),
    QueryModel(
        queries.mailshot_file_targets,
        "Mailshot File Targets",
        dm.FileTarget,
    ),
    QueryModel(
        queries.file_folders_folder_type,
        "Import Application Case Note File Folders",
        dm.FileFolder,
        {"folder_type": "IMP_CASE_NOTE_DOCUMENTS"},
    ),
    QueryModel(
        queries.file_targets_folder_type,
        "Import Application Case Note File Targets",
        dm.FileTarget,
        {"folder_type": "IMP_CASE_NOTE_DOCUMENTS"},
    ),
    QueryModel(
        queries.file_folders_folder_type,
        "GMP Application File Folders",
        dm.FileFolder,
        {"folder_type": "GMP_SUPPORTING_DOCUMENTS"},
    ),
    QueryModel(
        queries.file_targets_folder_type,
        "GMP Application File Targets",
        dm.FileTarget,
        {"folder_type": "GMP_SUPPORTING_DOCUMENTS"},
    ),
    QueryModel(
        queries.export_case_note_folders,
        "Export Application Case Note Document Folders",
        dm.DocFolder,
    ),
]

file_query_model = [
    QueryModel(
        queries.import_application_files,
        "SPS Application Files",
        dm.File,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
            "ima_type": "SPS",
            "ima_sub_type": "SPS1",
            "path_prefix": "sps_application_files",
        },
    ),
    QueryModel(
        queries.import_application_files,
        "FA-DFL Application Files",
        dm.File,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
            "ima_type": "FA",
            "ima_sub_type": "DEACTIVATED",
            "path_prefix": "dfl_application_files",
        },
    ),
    QueryModel(
        queries.import_application_files,
        "FA-OIL Application Files",
        dm.File,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
            "ima_type": "FA",
            "ima_sub_type": "OIL",
            "path_prefix": "oil_application_files",
        },
    ),
    QueryModel(
        queries.import_application_files,
        "FA-SIL Application Files",
        dm.File,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
            "ima_type": "FA",
            "ima_sub_type": "SIL",
            "path_prefix": "sil_application_files",
        },
    ),
    QueryModel(
        queries.import_application_files,
        "Sanctions & Adhoc Application Files",
        dm.File,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
            "ima_type": "ADHOC",
            "ima_sub_type": "ADHOC1",
            "path_prefix": "sanctions_application_files",
        },
    ),
    QueryModel(
        queries.import_application_files,
        "OPT Application Files",
        dm.File,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
            "ima_type": "OPT",
            "ima_sub_type": "QUOTA",
            "path_prefix": "opt_application_files",
        },
    ),
    QueryModel(
        queries.import_application_files,
        "Wood Application Files",
        dm.File,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
            "ima_type": "WD",
            "ima_sub_type": "QUOTA",
            "path_prefix": "wood_application_files",
        },
    ),
    QueryModel(
        queries.import_application_files,
        "Textiles Application Files",
        dm.File,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
            "ima_type": "TEX",
            "ima_sub_type": "QUOTA",
            "path_prefix": "textiles_application_files",
        },
    ),
    QueryModel(
        queries.fa_certificate_files,
        "Firearms & Ammunition Certificate Files",
        dm.File,
        {"secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID, "path_prefix": "fa_certificate_files"},
    ),
    QueryModel(
        queries.fir_files,
        "Further Information Request Files",
        dm.File,
        {"secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID, "path_prefix": "fir_files"},
    ),
    QueryModel(
        queries.mailshot_files,
        "Mailshot Files",
        dm.File,
        {"secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID, "path_prefix": "mailshot_files"},
    ),
    QueryModel(
        queries.gmp_application_files,
        "GMP Application Files",
        dm.File,
        {"secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID},
    ),
    QueryModel(
        queries.file_objects_folder_type,
        "Import Application Case Note Files",
        dm.File,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
            "folder_type": "IMP_CASE_NOTE_DOCUMENTS",
            "path_prefix": "import_application_case_note_files",
        },
    ),
    QueryModel(
        queries.export_case_note_docs,
        "Export Application Case Note Documents",
        dm.File,
        {"secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID},
    ),
    QueryModel(
        queries.fa_supplementary_report_upload_files,
        "Supplementary Report Goods Uploaded Files",
        dm.File,
        {
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
        },
        "created_datetime",
    ),
    QueryModel(
        queries.ia_licence_docs,
        "Import Application Licence Documents",
        dm.CaseDocument,
        {"secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID},
    ),
    QueryModel(
        queries.export_certificate_docs,
        "Export Application Certificate Documents",
        dm.ExportCertificateCaseDocumentReferenceData,
        {
            "secure_lob_ref_id": DEFAULT_SECURE_LOB_REF_ID,
        },
    ),
]

file_m2m = [
    M2M(dm.MailshotDoc, web.Mailshot, "documents"),
    M2M(dm.ConstabularyEmailAttachments, web.CaseEmail, "attachments"),
    M2M(dm.FIRFile, web.FurtherInformationRequest, "files"),
    M2M(dm.CaseNoteFile, web.CaseNote, "files"),
    M2M(dm.FirearmsAuthorityFile, web.FirearmsAuthority, "files"),
    M2M(dm.Section5AuthorityFile, web.Section5Authority, "files"),
    M2M(
        dm.SPSSupportingDoc,
        web.PriorSurveillanceApplication,
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
    M2M(
        dm.GMPFile,
        web.CertificateOfGoodManufacturingPracticeApplication,
        "supporting_documents",
    ),
]

file_source_target = [
    SourceTarget(dm.File, web.File),
    SourceTarget(dm.DFLGoodsCertificate, web.DFLGoodsCertificate),
    SourceTarget(dm.DFLSupplementaryReportFirearm, web.DFLSupplementaryReportFirearm),
    SourceTarget(dm.OILSupplementaryReportFirearm, web.OILSupplementaryReportFirearm),
    SourceTarget(dm.UserImportCertificate, web.UserImportCertificate),
    SourceTarget(dm.SILUserSection5, web.SILUserSection5),
    SourceTarget(dm.PriorSurveillanceContractFile, web.PriorSurveillanceContractFile),
    SourceTarget(dm.PriorSurveillanceApplication, web.PriorSurveillanceApplication),
    SourceTarget(dm.OutwardProcessingTradeFile, web.OutwardProcessingTradeFile),
    SourceTarget(dm.WoodContractFile, web.WoodContractFile),
    SourceTarget(dm.GMPFile, web.GMPFile),
    SourceTarget(dm.ImportCaseDocument, web.CaseDocumentReference),
    SourceTarget(dm.ExportCaseDocument, web.CaseDocumentReference),
    SourceTarget(
        dm.ExportCertificateCaseDocumentReferenceData,
        web.ExportCertificateCaseDocumentReferenceData,
    ),
]
