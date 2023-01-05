# TODO: Look at statuses again

ia_licence = """
SELECT
  ir.ima_id
  , ird.imad_id
  , ird.licence_start_date
  , ird.licence_end_date
  , CASE
    WHEN ird.variation_no > 0
    THEN ia.case_ref || '/' || ird.variation_no
    ELSE ia.case_ref
  END case_reference
  , CASE xiad.print_documents_flag WHEN 'Y' THEN 1 ELSE 0 END issue_paper_licence_only
  , ird.id legacy_id
  , CASE
    WHEN xiad.status IN ('REVOKED', 'WITHDRAWN', 'STOPPED') THEN 'AR'
    WHEN ird.variation_no < xiad.variation_no THEN 'AR'
    WHEN xiad.status IN ('PROCESSING', 'VARIATION_REQUESTED', 'SUBMITTED') THEN 'DR'
    ELSE 'AC'
  END status
  , ir.created_datetime created_at
  , ird.start_datetime case_completion_datetime
FROM impmgr.ima_responses ir
  INNER JOIN impmgr.ima_response_details ird ON ird.ir_id = ir.id
  INNER JOIN impmgr.import_applications ia ON ia.id = ir.ima_id
  INNER JOIN impmgr.xview_ima_details xiad ON xiad.ima_id = ia.id AND xiad.status_control = 'C'
WHERE ir.response_type LIKE '%_LICENCE'
ORDER BY ird.id
"""

#  , dd.signed_datetime
#  , dd.signed_by_id signed_by_str

ia_licence_docs = r"""
WITH wua_login AS (
  SELECT distinct wua_id, login_id
  FROM securemgr.web_user_account_histories
  GROUP BY wua_id, login_id
)
SELECT
  ird.imad_id licence_id
  , dd.id document_legacy_id
  , CASE
      WHEN ir.response_type LIKE '%_COVER' THEN ''
      WHEN xiad.print_documents_flag = 'Y' THEN ''
      ELSE iat.chief_licence_prefix
  END || ir.licence_ref || ir.licence_check_letter reference
  , CASE WHEN ir.response_type LIKE '%_COVER' THEN 'COVER_LETTER' ELSE 'LICENCE' END document_type
  , xdd.title filename
  , xdd.content_type
  , dbms_lob.getlength(sld.blob_data) file_size
  , sld.id || '-' || xdd.title path
  , dd.created_datetime
  , dd.created_by created_by_str
  , wl.wua_id created_by_id
FROM impmgr.ima_responses ir
  INNER JOIN impmgr.ima_response_details ird ON ird.ir_id = ir.id
  INNER JOIN impmgr.xview_ima_details xiad ON xiad.imad_id = ird.imad_id
  INNER JOIN impmgr.import_application_types iat ON iat.ima_type = xiad.ima_type AND iat.ima_sub_type = xiad.ima_sub_type
  INNER JOIN impmgr.xview_ima_rd_di_details xird ON xird.ird_id = ird.id
  INNER JOIN decmgr.xview_document_data xdd ON xdd.di_id = xird.di_id AND xdd.system_document = 'N' AND xdd.content_description = 'PDF'
  INNER JOIN decmgr.document_data dd ON dd.id = xdd.dd_id
  INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(dd.secure_lob_ref).id
  INNER JOIN wua_login wl ON wl.login_id = REGEXP_SUBSTR(dd.created_by, '\((.+)\)', 1, 1, NULL, 1)
WHERE ir.response_type LIKE '%_LICENCE' OR ir.response_type LIKE '%_COVER'
ORDER BY sld.id
"""

ia_timestamp_update = """
UPDATE web_importapplication SET create_datetime = data_migration_importapplication.create_datetime
FROM data_migration_importapplication
WHERE web_importapplication.process_ptr_id = data_migration_importapplication.id
"""

ia_licence_timestamp_update = """
UPDATE web_importapplicationlicence SET created_at = data_migration_importapplicationlicence.created_at
FROM data_migration_importapplicationlicence
WHERE web_importapplicationlicence.id = data_migration_importapplicationlicence.id
"""
