import_application_subquery = """
  SELECT DISTINCT app_docs_ff_id
    FROM impmgr.xview_ima_details xid
      INNER JOIN impmgr.import_application_types iat
        ON iat.ima_type = xid.ima_type AND iat.ima_sub_type = xid.ima_sub_type
    WHERE xid.status <> 'DELETED'
      AND xid.ima_type = :ima_type
      AND xid.ima_sub_type = :ima_sub_type
      AND (
        (iat.status = 'ARCHIVED' AND xid.submitted_datetime IS NOT NULL)
        OR (
          iat.status = 'CURRENT'
          AND (xid.submitted_datetime IS NOT NULL OR xid.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
        )
      )
"""


import_application_folders = f"""
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , :app_model app_model
FROM decmgr.file_folders ff
INNER JOIN ({import_application_subquery}) xid ON xid.app_docs_ff_id = ff.id
ORDER by ff.id
"""


import_application_file_targets = f"""
SELECT
  ff_id folder_id
  , fft.target_mnem target_type
  , fft.status
  , fft.id target_id
FROM decmgr.file_folder_targets fft
INNER JOIN ({import_application_subquery}) xid ON fft.ff_id = xid.app_docs_ff_id
ORDER by fft.id
"""


import_application_files = f"""
SELECT
  fft.id target_id
  , fv.*
  , sld.blob_data
FROM decmgr.file_folder_targets fft
INNER JOIN ({import_application_subquery}) xid ON fft.ff_id = xid.app_docs_ff_id
INNER JOIN (
  SELECT
    fft_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , create_by_wua_id created_by_id
    , TO_CHAR(:path_prefix) || '/' || TO_CHAR(id) || '-' || x.filename path
    , DEREF(secure_lob_ref).id  secure_lob_ref_id
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
INNER JOIN securemgr.secure_lob_data sld ON sld.id = fv.secure_lob_ref_id
WHERE created_datetime > TO_DATE(:created_datetime, 'YYYY-MM-DD HH24:MI:SS')
ORDER by fft.id
"""


file_folders_base = """
SELECT DISTINCT
  ff.id folder_id
  , ff.file_folder_type folder_type
FROM {from_table}
INNER JOIN decmgr.file_folders ff ON xx.{folder_column} = ff.id
ORDER by ff.id
"""


file_targets_base = """
SELECT DISTINCT
  ff.id folder_id
  , fft.target_mnem target_type
  , fft.id target_id
  , fft.status
FROM {from_table}
INNER JOIN decmgr.file_folders ff ON xx.{folder_column} = ff.id
INNER JOIN decmgr.file_folder_targets fft ON fft.ff_id = ff.id
ORDER by fft.id
"""


file_objects_base = """
SELECT
  fft.id target_id
  , fv.version_id
  , fv.filename
  , fv.content_type
  , fv.file_size
  , fv.path
  , created_datetime
  , fv.created_by_id
  , sld.blob_data
FROM {from_table}
INNER JOIN decmgr.file_folders ff ON xx.{folder_column} = ff.id
INNER JOIN decmgr.file_folder_targets fft ON fft.ff_id = ff.id
INNER JOIN (
  SELECT
    fft_id target_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , create_by_wua_id created_by_id
    , TO_CHAR(:path_prefix) || '/' || TO_CHAR(id) || '-' || x.filename path
    , DEREF(secure_lob_ref).id  secure_lob_ref_id
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
INNER JOIN securemgr.secure_lob_data sld ON sld.id = secure_lob_ref_id
WHERE created_datetime > TO_DATE(:created_datetime, 'YYYY-MM-DD HH24:MI:SS'){condition}
ORDER by fft.id
"""

folder_column = "file_folder_id"

fa_certificate_files_from = """impmgr.importer_authorities ia
INNER JOIN (
  SELECT ia_id, x.*
  FROM impmgr.importer_authority_details iad,
    XMLTABLE('/*'
    PASSING iad.xml_data
    COLUMNS
      file_folder_id INTEGER PATH '/AUTHORITY/DOCUMENTS_FF_ID/text()'
    ) x
  WHERE iad.status_control = 'C'
) xx ON xx.ia_id = ia.id"""

fa_certificate_folders = file_folders_base.format(
    from_table=fa_certificate_files_from, folder_column=folder_column
)
fa_certificate_file_targets = file_targets_base.format(
    from_table=fa_certificate_files_from, folder_column=folder_column
)
fa_certificate_files = file_objects_base.format(
    from_table=fa_certificate_files_from, condition="", folder_column=folder_column
)


fir_files_from = "impmgr.xview_ima_rfis xx"
fir_files_condition = " AND xx.status_control = 'C'"
fir_file_folders = file_folders_base.format(from_table=fir_files_from, folder_column=folder_column)
fir_file_targets = file_targets_base.format(from_table=fir_files_from, folder_column=folder_column)
fir_files = file_objects_base.format(
    from_table=fir_files_from, condition=fir_files_condition, folder_column=folder_column
)

mailshot_files_from = "mailshotmgr.xview_mailshot_details xx"
mailshot_files_condition = " AND xx.status_control = 'C'"
mailshot_file_folders = file_folders_base.format(
    from_table=mailshot_files_from, folder_column="documents_ff_id"
)
mailshot_file_targets = file_targets_base.format(
    from_table=mailshot_files_from, folder_column="documents_ff_id"
)
mailshot_files = file_objects_base.format(
    from_table=mailshot_files_from,
    condition=mailshot_files_condition,
    folder_column="documents_ff_id",
)


file_folders_folder_type = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
FROM decmgr.file_folders ff
WHERE ff.file_folder_type = :folder_type
ORDER by ff.id
"""

file_targets_folder_type = """
SELECT
  ff.id folder_id
  , fft.target_mnem target_type
  , fft.id target_id
  , fft.status
FROM decmgr.file_folder_targets fft
INNER JOIN decmgr.file_folders ff ON fft.ff_id = ff.id
WHERE ff.file_folder_type = :folder_type
ORDER by fft.id
"""

file_objects_folder_type = """
SELECT
  fft.id target_id
  , fv.version_id
  , fv.filename
  , fv.content_type
  , fv.file_size
  , fv.path
  , created_datetime
  , fv.created_by_id
  , sld.blob_data
FROM decmgr.file_folder_targets fft
INNER JOIN decmgr.file_folders ff ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id target_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , create_by_wua_id created_by_id
    , TO_CHAR(:path_prefix) || '/' || id || '-' || x.filename path
    , DEREF(secure_lob_ref).id  secure_lob_ref_id
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
INNER JOIN securemgr.secure_lob_data sld ON sld.id = secure_lob_ref_id
WHERE created_datetime > TO_DATE(:created_datetime, 'YYYY-MM-DD HH24:MI:SS')
AND ff.file_folder_type = :folder_type
ORDER by fft.id
"""

export_case_note_folders = """
SELECT
  fd.f_id doc_folder_id
  , fd.folder_title
FROM doclibmgr.folder_details fd
WHERE fd.folder_title LIKE 'Case Note %'
"""

export_case_note_docs = """
SELECT
  fd.f_id doc_folder_id
  , fv.id version_id
  , vf.filename
  , vf.content_type
  , vf.created_datetime as created_datetime
  , vf.created_by_wua_id created_by_id
  , EXTRACTVALUE(vf.metadata_xml, '/file-metadata/size') file_size
  , 'export_case_note_docs/' || vf.file_id || '-' || vf.filename path
  , sld.blob_data
FROM doclibmgr.folder_details fd
INNER JOIN doclibmgr.vw_file_folders vff ON vff.f_id = fd.f_id
INNER JOIN doclibmgr.vw_files vf ON vf.file_id = vff.file_id
INNER JOIN doclibmgr.file_versions fv ON fv.file_id = vf.file_id
INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(vf.secure_lob_ref).id
WHERE fd.folder_title LIKE 'Case Note %'
  AND vf.created_datetime > TO_DATE(:created_datetime, 'YYYY-MM-DD HH24:MI:SS')
ORDER BY vf.file_id
"""


fa_supplementary_report_upload_files = """
SELECT
  'fa_supplementary_report_upload_files/' || x.sr_goods_file_id || '/' || x.filename PATH
  , glf.file_content as blob_data
  , to_date(replace(created_datetime_str, 'T', chr(10)), 'YYYY-MM-DD HH24:MI:SS') created_datetime
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
  , created_datetime_str VARCHAR(4000) PATH '/uploads/created_datetime/text()'
) x
INNER JOIN impmgr.goods_line_files glf ON glf.id = x.sr_goods_file_id
WHERE ad.status_control = 'C'
AND TO_DATE(created_datetime_str, 'YYYY-MM-DD"T"HH24:MI:SS') > TO_DATE (:created_datetime, 'YYYY-MM-DD HH24:MI:SS')
ORDER BY glf.id
"""


file_timestamp_update = """
UPDATE web_file SET created_datetime = data_migration_file.created_datetime
FROM data_migration_file
WHERE web_file.id = data_migration_file.id
"""
