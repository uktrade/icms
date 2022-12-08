__all__ = [
    "case_note_files",
    "derogations_application_files",
    "dfl_application_files",
    "export_case_note_docs",
    "fa_certificate_files",
    "fir_files",
    "gmp_files",
    "mailshot_files",
    "oil_application_files",
    "opt_application_files",
    "sanction_application_files",
    "sil_application_files",
    "sps_application_files",
    "sps_docs",
    "textiles_application_files",
    "wood_application_files",
]


# Join to SECURE_LOB_DATA when retrieving the file data
# INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(fv.secure_lob_ref).id

import_application_files_base = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , '{app_model}' app_model
  , fft.target_mnem target_type
  , fft.status
  , fft.id target_id
  , fv.*
FROM impmgr.xview_ima_details xid
INNER JOIN impmgr.import_application_types iat
  ON iat.ima_type = xid.ima_type AND iat.ima_sub_type = xid.ima_sub_type
INNER JOIN decmgr.file_folders ff ON ff.id = xid.app_docs_ff_id
LEFT JOIN decmgr.file_folder_targets fft ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , create_by_wua_id created_by_id
    , CONCAT(id, CONCAT('-', x.filename)) path
    , x.*
  FROM decmgr.file_versions fv
  CROSS JOIN XMLTABLE('/*'
    PASSING fv.metadata_xml
    COLUMNS
      filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
      , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
      , file_size NUMBER PATH '/file-metadata/size/text()'
  ) x
  WHERE status_control = 'C'
) fv ON fv.fft_id = fft.id
WHERE fft.target_mnem IN ({target_types})
AND xid.ima_type = '{ima_type}'
AND xid.ima_sub_type = '{ima_sub_type}'
AND xid.status_control = 'C'
AND xid.status <> 'DELETED'
AND (
  (iat.status = 'ARCHIVED' AND xid.submitted_datetime IS NOT NULL)
  OR (
    iat.status = 'CURRENT'
    AND (xid.submitted_datetime IS NOT NULL OR xid.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
  )
)
ORDER by fft.id
"""


derogations_application_files = import_application_files_base.format(
    **{
        "ima_type": "SAN",
        "ima_sub_type": "SAN1",
        "app_model": "derogationsapplication",
        "target_types": "'IMP_SUPPORTING_DOC'",
    }
)

sps_application_files = import_application_files_base.format(
    **{
        "ima_type": "SPS",
        "ima_sub_type": "SPS1",
        "app_model": "priorsurveillanceapplication",
        "target_types": "'IMP_SUPPORTING_DOC'",
    }
)

dfl_application_files = import_application_files_base.format(
    **{
        "ima_type": "FA",
        "ima_sub_type": "DEACTIVATED",
        "app_model": "dflapplication",
        "target_types": "'IMP_FIREARMS_CERTIFICATE'",
    }
)

oil_application_files = import_application_files_base.format(
    **{
        "ima_type": "FA",
        "ima_sub_type": "OIL",
        "app_model": "openindividuallicenceapplication",
        "target_types": "'IMP_FIREARMS_CERTIFICATE', 'IMP_SECTION5_AUTHORITY'",
    }
)

sil_application_files = import_application_files_base.format(
    **{
        "ima_type": "FA",
        "ima_sub_type": "SIL",
        "app_model": "silapplication",
        "target_types": "'IMP_FIREARMS_CERTIFICATE', 'IMP_SECTION5_AUTHORITY'",
    }
)

sanction_application_files = import_application_files_base.format(
    **{
        "ima_type": "ADHOC",
        "ima_sub_type": "ADHOC1",
        "app_model": "sanctionsandadhocapplication",
        "target_types": "'IMP_SUPPORTING_DOC', 'IMP_CONTRACT_DOC'",
    }
)

opt_application_files = import_application_files_base.format(
    **{
        "ima_type": "OPT",
        "ima_sub_type": "QUOTA",
        "app_model": "outwardprocessingtradeapplication",
        "target_types": (
            "'IMP_SUPPORTING_DOC', 'IMP_OPT_BENEFICIARY_DOC', 'IMP_OPT_EMPLOY_DOC', "
            "'IMP_OPT_FURTHER_AUTH_DOC','IMP_OPT_NEW_APP_JUST_DOC', "
            "'IMP_OPT_PRIOR_AUTH_DOC', 'IMP_OPT_SUBCONTRACT_DOC'"
        ),
    }
)

wood_application_files = import_application_files_base.format(
    **{
        "ima_type": "WD",
        "ima_sub_type": "QUOTA",
        "app_model": "woodquotaapplication",
        "target_types": "'IMP_CONTRACT_DOC', 'IMP_SUPPORTING_DOC'",
    }
)

textiles_application_files = import_application_files_base.format(
    **{
        "ima_type": "TEX",
        "ima_sub_type": "QUOTA",
        "app_model": "textilesapplication",
        "target_types": "'IMP_CONTRACT_DOC', 'IMP_SUPPORTING_DOC'",
    }
)

fa_certificate_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , fft.target_mnem target_type
  , fft.id target_id
  , fft.status
  , fv.version_id
  , fv.filename
  , fv.content_type
  , fv.file_size
  , fv.path
  , created_datetime
  , fv.created_by_id
FROM impmgr.importer_authorities ia
INNER JOIN (
  SELECT ia_id, x.*
  FROM impmgr.importer_authority_details iad,
    XMLTABLE('/*'
    PASSING iad.xml_data
    COLUMNS
      file_folder_id INTEGER PATH '/AUTHORITY/DOCUMENTS_FF_ID/text()'
    ) x
  WHERE iad.status_control = 'C'
) iad ON iad.ia_id = ia.id
INNER JOIN decmgr.file_folders ff ON iad.file_folder_id = ff.id
LEFT JOIN decmgr.file_folder_targets fft ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id target_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , create_by_wua_id created_by_id
    , CONCAT(id, CONCAT('-', x.filename)) path
    , x.*
  FROM decmgr.file_versions fv
  CROSS JOIN XMLTABLE('/*'
    PASSING metadata_xml
    COLUMNS
      filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
      , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
      , file_size NUMBER PATH '/file-metadata/size/text()'
    ) x
  WHERE status_control = 'C'
) fv ON fv.target_id = fft.id
ORDER by fft.id
"""

sps_docs = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , 'priorsurveillanceapplication' app_model
  , fft.target_mnem target_type
  , fft.id target_id
  , fft.status
  , fv.version_id
  , fv.filename
  , fv.content_type
  , fv.file_size
  , fv.path
  , created_datetime
  , fv.created_by_id
FROM decmgr.file_folder_targets fft
INNER JOIN decmgr.file_folders ff ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id target_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , create_by_wua_id created_by_id
    , CONCAT(id, CONCAT('-', x.filename)) path
    , x.*
  FROM decmgr.file_versions fv,
    XMLTABLE('/*'
    PASSING metadata_xml
    COLUMNS
      filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
      , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
      , file_size NUMBER PATH '/file-metadata/size/text()'
    ) x
  WHERE status_control = 'C'
 ) fv ON fv.target_id = fft.ID
WHERE fft.target_mnem = 'IMP_SPS_DOC'
AND fft.status = 'RECEIVED'
ORDER by fft.id
"""


case_note_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , fft.target_mnem target_type
  , fft.id target_id
  , fft.status
  , fv.version_id
  , fv.filename
  , fv.content_type
  , fv.file_size
  , fv.path
  , created_datetime
  , fv.created_by_id
FROM decmgr.file_folder_targets fft
INNER JOIN decmgr.file_folders ff ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id target_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , create_by_wua_id created_by_id
    , CONCAT(id, CONCAT('-', x.filename)) path
    , x.*
  FROM decmgr.file_versions fv
  CROSS JOIN XMLTABLE('/*'
    PASSING metadata_xml
    COLUMNS
      filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
      , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
      , file_size NUMBER PATH '/file-metadata/size/text()'
    ) x
  WHERE status_control = 'C'
 ) fv ON fv.target_id = fft.ID
WHERE ff.file_folder_type = 'IMP_CASE_NOTE_DOCUMENTS'
ORDER by fft.id
"""


fir_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , fft.target_mnem target_type
  , fft.id target_id
  , fft.status
  , fv.version_id
  , fv.filename
  , fv.content_type
  , fv.file_size
  , fv.path
  , created_datetime
  , fv.created_by_id
FROM impmgr.xview_ima_rfis xir
INNER JOIN decmgr.file_folders ff ON ff.id = xir.file_folder_id
LEFT JOIN decmgr.file_folder_targets fft ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id target_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , create_by_wua_id created_by_id
    , CONCAT(id, CONCAT('-', x.filename)) path
    , x.*
  FROM decmgr.file_versions fv
  CROSS JOIN XMLTABLE('/*'
    PASSING metadata_xml
    COLUMNS
      filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
      , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
      , file_size NUMBER PATH '/file-metadata/size/text()'
    ) x
  WHERE status_control = 'C'
 ) fv ON fv.target_id = fft.ID
ORDER by fft.id
 """


mailshot_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , fft.target_mnem target_type
  , fft.id target_id
  , fft.status
  , fv.version_id
  , fv.filename
  , fv.content_type
  , fv.file_size
  , fv.path
  , created_datetime
  , fv.created_by_id
FROM mailshotmgr.xview_mailshot_details xmd
INNER JOIN decmgr.file_folders ff ON ff.id = xmd.documents_ff_id
LEFT JOIN decmgr.file_folder_targets fft ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id target_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , create_by_wua_id created_by_id
    , CONCAT(id, CONCAT('-', x.filename)) path
    , x.*
  FROM decmgr.file_versions fv
  CROSS JOIN XMLTABLE('/*'
    PASSING metadata_xml
    COLUMNS
      filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
      , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
      , file_size NUMBER PATH '/file-metadata/size/text()'
    ) x
  WHERE status_control = 'C'
 ) fv ON fv.target_id = fft.ID
WHERE xmd.status_control = 'C'
ORDER by fft.id
"""


gmp_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , fft.target_mnem target_type
  , fft.id target_id
  , fft.status
  , fv.version_id
  , fv.filename
  , fv.content_type
  , fv.file_size
  , fv.path
  , created_datetime
  , fv.created_by_id
FROM decmgr.file_folder_targets fft
INNER JOIN decmgr.file_folders ff ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id target_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , create_by_wua_id created_by_id
    , CONCAT(id, CONCAT('-', x.filename)) path
    , x.*
  FROM decmgr.file_versions fv
  CROSS JOIN XMLTABLE('/*'
    PASSING metadata_xml
    COLUMNS
      filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
      , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
      , file_size NUMBER PATH '/file-metadata/size/text()'
    ) x
  WHERE status_control = 'C'
 ) fv ON fv.target_id = fft.ID
WHERE ff.file_folder_type = 'GMP_SUPPORTING_DOCUMENTS'
ORDER by fft.id
"""


# To access blob file in secure_lob_data
# INNER JOIN DOCLIBMGR.FILE_versions fv ON fv.id = vf.file_id
# INNER JOIN securemgr.secure_lob_data sld ON sld.id = vf.secure_lob_id

export_case_note_docs = """
SELECT
  fd.f_id doc_folder_id
  , fd.folder_title
  , vf.file_id
  , vf.filename
  , vf.content_type
  , vf.created_datetime
  , vf.created_by_wua_id created_by_id
  , EXTRACTVALUE(vf.metadata_xml, '/file-metadata/size') file_size
  , vf.file_id || '-' || vf.filename path
FROM doclibmgr.folder_details fd
LEFT JOIN doclibmgr.vw_file_folders vff ON vff.f_id = fd.f_id
LEFT JOIN doclibmgr.vw_files vf ON vf.file_id = vff.file_id
WHERE fd.folder_title LIKE 'Case Note %'
ORDER BY vf.file_id
"""
