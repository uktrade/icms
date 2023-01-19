# Join to SECURE_LOB_DATA when retrieving the file data
# INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(fv.secure_lob_ref).id

derogations_application_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , 'derogationsapplication' app_model
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
WHERE fft.target_mnem IN ('IMP_SUPPORTING_DOC')
AND xid.ima_type = 'SAN'
AND xid.ima_sub_type = 'SAN1'
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

sps_application_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , 'priorsurveillanceapplication' app_model
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
WHERE fft.target_mnem IN ('IMP_SUPPORTING_DOC')
AND xid.ima_type = 'SPS'
AND xid.ima_sub_type = 'SPS1'
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


dfl_application_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , 'dflapplication' app_model
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
WHERE fft.target_mnem IN ('IMP_FIREARMS_CERTIFICATE')
AND xid.ima_type = 'FA'
AND xid.ima_sub_type = 'DEACTIVATED'
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


oil_application_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , 'openindividuallicenceapplication' app_model
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
WHERE fft.target_mnem IN ('IMP_FIREARMS_CERTIFICATE', 'IMP_SECTION5_AUTHORITY')
AND xid.ima_type = 'FA'
AND xid.ima_sub_type = 'OIL'
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


sil_application_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , 'silapplication' app_model
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
WHERE fft.target_mnem IN ('IMP_FIREARMS_CERTIFICATE', 'IMP_SECTION5_AUTHORITY')
AND xid.ima_type = 'FA'
AND xid.ima_sub_type = 'SIL'
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


sanction_application_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , 'sanctionsandadhocapplication' app_model
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
WHERE fft.target_mnem IN ('IMP_SUPPORTING_DOC', 'IMP_CONTRACT_DOC')
AND xid.ima_type = 'ADHOC'
AND xid.ima_sub_type = 'ADHOC1'
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


opt_application_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , 'outwardprocessingtradeapplication' app_model
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
WHERE fft.target_mnem IN (
  'IMP_SUPPORTING_DOC', 'IMP_OPT_BENEFICIARY_DOC', 'IMP_OPT_EMPLOY_DOC', 'IMP_OPT_FURTHER_AUTH_DOC',
  'IMP_OPT_NEW_APP_JUST_DOC', 'IMP_OPT_PRIOR_AUTH_DOC', 'IMP_OPT_SUBCONTRACT_DOC'
)
AND xid.ima_type = 'OPT'
AND xid.ima_sub_type = 'QUOTA'
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


wood_application_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , 'woodquotaapplication' app_model
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
WHERE fft.target_mnem IN ('IMP_CONTRACT_DOC', 'IMP_SUPPORTING_DOC')
AND xid.ima_type = 'WD'
AND xid.ima_sub_type = 'QUOTA'
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


textiles_application_files = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , 'textilesapplication' app_model
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
WHERE fft.target_mnem IN ('IMP_CONTRACT_DOC', 'IMP_SUPPORTING_DOC')
AND xid.ima_type = 'TEX'
AND xid.ima_sub_type = 'QUOTA'
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


fa_supplementary_report_upload_files = """
SELECT
  ad.ima_id
  , ad.id imad_id
  , CONCAT(id, CONCAT('/', x.filename)) path
  , x.*
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_type = 'FA'
CROSS JOIN XMLTABLE('
for $g1 in /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT | <null/>
where /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT and not($g1/self::null)
return
for $g2 in $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE | <null/>
where $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE and not($g2/self::null)
return
for $g3 in $g2/FILE_UPLOAD_LIST/FILE_UPLOAD | <null/>
where $g2/FILE_UPLOAD_LIST/FILE_UPLOAD and not ($g3/self::null)
return
<uploads>
  <report_mode>{$g2/FA_REPORTING_MODE/text()}</report_mode>
  <created_by_id>{$g1/FA_SUPPLEMENTARY_REPORT_DETAILS/SUBMITTED_BY_WUA_ID/text()}</created_by_id>
  <file_id>{$g3/FILE_CONTENT/file-id/text()}</file_id>
  <file_size>{$g3/FILE_CONTENT/size/text()}</file_size>
  <filename>{$g3/FILE_CONTENT/filename/text()}</filename>
  <content_type>{$g3/FILE_CONTENT/content-type/text()}</content_type>
  <created_datetime>{$g3/FILE_CONTENT/upload-date-time/text()}</created_datetime>
</uploads>
'
PASSING ad.xml_data
COLUMNS
  created_by_id INTEGER PATH '/uploads/created_by_id/text()'
  , sr_goods_file_id VARCHAR(4000) PATH '/uploads/file_id/text()'
  , file_size INTEGER PATH '/uploads/file_size/text()'
  , filename VARCHAR(4000) PATH '/uploads/filename/text()'
  , content_type VARCHAR(4000) PATH '/uploads/content_type/text()'
  , created_datetime VARCHAR(4000) PATH '/uploads/created_datetime/text()'
) x
WHERE ad.status_control = 'C'
"""

# INNER JOIN impmgr.goods_line_files glf ON glf.id = x.sr_goods_file_id  <- to access blob file


file_timestamp_update = """
UPDATE web_file SET created_datetime = data_migration_file.created_datetime
FROM data_migration_file
WHERE web_file.id = data_migration_file.id
"""
