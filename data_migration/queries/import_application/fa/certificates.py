# Join to SECURE_LOB_DATA when retrieving the file data
# created_by created_by_id
# INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(fv.secure_lob_ref).id


fa_file_target = """
SELECT
  fft.id
  , ff.file_folder_type folder_type
  , fft.target_mnem target_type
FROM decmgr.file_folder_targets fft
INNER JOIN decmgr.file_folders ff ON fft.ff_id = ff.id
WHERE fft.target_mnem IN ('IMP_FIREARMS_CERTIFICATE', 'IMP_FIREARMS_AUTHORITY', 'IMP_SECTION5_AUTHORITY')
"""


fa_certificates = """
SELECT
  fv.target_id
  , fv.filename
  , fv.content_type
  , fv.file_size
  , fv.path
  , created_datetime
  , 2 created_by_id
FROM decmgr.file_folder_targets fft
INNER JOIN (
  SELECT
    fft_id target_id
    , secure_lob_ref
    , status_control
    , create_start_datetime created_datetime
    , create_by_wua_id created_by
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
 ) fv ON fv.target_id = fft.ID
WHERE target_mnem  IN ('IMP_FIREARMS_CERTIFICATE', 'IMP_SECTION5_AUTHORITY')
AND fv.status_control = 'C'
"""
