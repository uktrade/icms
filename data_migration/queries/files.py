__all__ = [
    "derogations_application_files",
    "dfl_application_files",
    "fa_certificate_files",
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
# , create_by_wua_id created_by_id

import_application_files_base = """
SELECT
  ff.id folder_id
  , ff.file_folder_type folder_type
  , '{app_model}' app_model
  , fft.target_mnem target_type
  , fft.status
  , fft.id target_id
  , fv.*
FROM decmgr.file_folders ff
INNER JOIN (
  SELECT ad.ima_id, x.ff_id
  FROM impmgr.import_application_details ad,
    XMLTABLE('/*'
    PASSING ad.xml_data
    COLUMNS
      ff_id INTEGER PATH '/IMA/APP_METADATA/APP_DOCS_FF_ID/text()'
    ) x
  WHERE status_control = 'C'
) ima ON ima.ff_id = ff.id
INNER JOIN impmgr.xview_ima_details xid ON xid.ima_id = ima.ima_id AND xid.ima_type = '{ima_type}' AND xid.ima_sub_type = '{ima_sub_type}'
LEFT JOIN decmgr.file_folder_targets fft ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id
    , fv.id version_id
    , create_start_datetime created_datetime
    , 2 created_by_id
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
) fv ON fv.fft_id = fft.id
WHERE fft.target_mnem IN ({target_types})
"""

derogations_application_files = import_application_files_base.format(
    **{
        "ima_type": "SAN",
        "ima_sub_type": "SAN1",
        "app_model": "derogationsapplication",
        "target_types": "'IMP_SUPPORTING_DOC'",
    }
)

sps_application_files = (
    import_application_files_base.format(
        **{
            "ima_type": "SPS",
            "ima_sub_type": "SPS1",
            "app_model": "priorsurveillanceapplication",
            "target_types": "'IMP_SUPPORTING_DOC'",
        }
    )
    + "  AND xid.submitted_datetime IS NOT NULL"
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
  , 2 created_by_id
FROM decmgr.file_folder_targets fft
INNER JOIN decmgr.file_folders ff ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id target_id
    , fv.id version_id
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
  WHERE status_control = 'C'
 ) fv ON fv.target_id = fft.ID
WHERE fft.target_mnem IN ('IMP_FIREARMS_CERTIFICATE', 'IMP_FIREARMS_AUTHORITY', 'IMP_SECTION5_AUTHORITY')
AND ff.file_folder_type <> 'IMP_APP_DOCUMENTS'
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
  , 2 created_by_id
FROM decmgr.file_folder_targets fft
INNER JOIN decmgr.file_folders ff ON fft.ff_id = ff.id
LEFT JOIN (
  SELECT
    fft_id target_id
    , fv.id version_id
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
  WHERE status_control = 'C'
 ) fv ON fv.target_id = fft.ID
WHERE fft.target_mnem = 'IMP_SPS_DOC'
AND fft.status = 'RECEIVED'
"""
