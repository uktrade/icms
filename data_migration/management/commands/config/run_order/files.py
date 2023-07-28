from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands._types import QueryModel, source_target_list

DEFAULT_FILE_CREATED_DATETIME = "2013-01-01 01:00:00"

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
        queries.fa_certificate_folders,
        "Firearms & Ammunition Certificate File Folders",
        dm.FileFolder,
    ),
    QueryModel(
        queries.fir_file_folders,
        "Further Information Request File Folders",
        dm.FileFolder,
    ),
    QueryModel(
        queries.mailshot_file_folders,
        "Mailshot File Folders",
        dm.FileFolder,
    ),
    QueryModel(
        queries.file_folders_folder_type,
        "Import Application Case Note File Folders",
        dm.FileFolder,
        {"folder_type": "IMP_CASE_NOTE_DOCUMENTS"},
    ),
    QueryModel(
        queries.file_folders_folder_type,
        "GMP Application File Folders",
        dm.FileFolder,
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
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
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
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
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
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
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
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
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
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
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
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
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
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
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
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
            "ima_type": "TEX",
            "ima_sub_type": "QUOTA",
            "path_prefix": "textiles_application_files",
        },
    ),
    QueryModel(
        queries.fa_certificate_files,
        "Firearms & Ammunition Certificate Files",
        dm.File,
        {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
    ),
    QueryModel(
        queries.fir_files,
        "Further Information Request Files",
        dm.File,
        {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
    ),
    QueryModel(
        queries.mailshot_files,
        "Mailshot Files",
        dm.File,
        {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
    ),
    QueryModel(
        queries.file_objects_folder_type,
        "GMP Application Files",
        dm.File,
        {
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
            "folder_type": "GMP_SUPPORTING_DOCUMENTS",
        },
    ),
    QueryModel(
        queries.file_objects_folder_type,
        "Import Application Case Note Files",
        dm.File,
        {
            "created_datetime": DEFAULT_FILE_CREATED_DATETIME,
            "folder_type": "IMP_CASE_NOTE_DOCUMENTS",
        },
    ),
    QueryModel(
        queries.export_case_note_docs,
        "Export Application Case Note Documents",
        dm.File,
        {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
    ),
    QueryModel(
        queries.fa_supplementary_report_upload_files,
        "Supplmentary Report Goods Uploaded Files",
        dm.File,
        {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
    ),
    QueryModel(
        queries.ia_licence_docs,
        "Import Application Licence Documents",
        dm.CaseDocument,
        {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
    ),
    QueryModel(
        queries.export_certificate_docs,
        "Export Application Certificate Documents",
        dm.ExportCertificateCaseDocumentReferenceData,
        {"created_datetime": DEFAULT_FILE_CREATED_DATETIME},
    ),
]

file_source_target = source_target_list(["File"])
