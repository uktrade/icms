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
    WHEN xiad.status = 'REVOKED' THEN 'RE'
    WHEN xiad.status IN ('WITHDRAWN', 'STOPPED') THEN 'AR'
    WHEN ird.variation_no < xiad.variation_no THEN 'AR'
    WHEN xiad.status IN ('PROCESSING', 'VARIATION_REQUESTED', 'SUBMITTED') THEN 'DR'
    ELSE 'AC'
  END status
  , ir.created_datetime created_at
  , ird.start_datetime updated_at
  , ird.start_datetime case_completion_datetime
  , dp.dp_id document_pack_id
  , x.revoke_reason
  , CASE x.revoke_email_sent WHEN 'true' THEN 1 ELSE 0 END revoke_email_sent
FROM impmgr.ima_responses ir
  INNER JOIN impmgr.ima_response_details ird ON ird.ir_id = ir.id
  INNER JOIN impmgr.import_applications ia ON ia.id = ir.ima_id
  INNER JOIN impmgr.xview_ima_details xiad ON xiad.ima_id = ia.id AND xiad.status_control = 'C'
  INNER JOIN impmgr.import_application_details iad ON iad.id = xiad.imad_id
  LEFT JOIN decmgr.xview_document_packs dp ON dp.ds_id = ird.ds_id
  CROSS JOIN XMLTABLE(
    '/IMA/APP_PROCESSING/REVOKE'
    PASSING iad.xml_data
    COLUMNS
      revoke_email_sent VARCHAR2(20) PATH './EMAIL_FLAG/text()'
      , revoke_reason CLOB PATH './REASON/text()'
  ) x
WHERE ir.response_type LIKE '%_LICENCE'
ORDER BY ird.id
"""

#  , dd.signed_datetime
#  , dd.signed_by_id signed_by_str

ia_licence_docs = r"""
SELECT
  ird.imad_id licence_id
  , dd.id document_legacy_id
  , CASE
      WHEN ir.response_type LIKE '%_COVER' THEN ''
      WHEN xiad.print_documents_flag = 'Y' THEN ''
      ELSE iat.chief_licence_prefix
    END || ir.licence_ref || ir.licence_check_letter reference
  , CASE WHEN ir.response_type LIKE '%_COVER' THEN 'COVER_LETTER' ELSE 'LICENCE' END document_type
  , CASE WHEN ir.response_type LIKE '%_COVER' THEN 'cover-letter.pdf' ELSE 'import-licence.pdf' END filename
  , xdd.content_type
  , dbms_lob.getlength(sld.blob_data) file_size
  , CASE
      WHEN ir.response_type LIKE '%_COVER'
      THEN 'import_cover_letter/' || sld.id || '-' || 'cover-letter.pdf'
      ELSE 'import_licence/' || sld.id || '-' || 'import-licence.pdf'
    END path
  , dd.created_datetime
  , dd.created_by created_by_str
  , wl.wua_id created_by_id
  , sld.blob_data
  , sld.id AS secure_lob_ref_id
FROM impmgr.ima_responses ir
  INNER JOIN impmgr.ima_response_details ird ON ird.ir_id = ir.id
  INNER JOIN impmgr.xview_ima_details xiad ON xiad.imad_id = ird.imad_id
  INNER JOIN impmgr.import_application_types iat ON iat.ima_type = xiad.ima_type AND iat.ima_sub_type = xiad.ima_sub_type
  INNER JOIN impmgr.xview_ima_rd_di_details xird ON xird.ird_id = ird.id
  INNER JOIN decmgr.xview_document_data xdd ON xdd.di_id = xird.di_id AND xdd.system_document = 'N' AND xdd.content_description = 'PDF'
  INNER JOIN decmgr.document_data dd ON dd.id = xdd.dd_id
  INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(dd.secure_lob_ref).id
  INNER JOIN (
    SELECT distinct wua_id, login_id
    FROM securemgr.web_user_account_histories
    GROUP BY wua_id, login_id
  ) wl ON wl.login_id = REGEXP_SUBSTR(dd.created_by, '\((.+)\)', 1, 1, NULL, 1)
WHERE (ir.response_type LIKE '%_LICENCE' OR ir.response_type LIKE '%_COVER')
  AND sld.id > :secure_lob_ref_id
ORDER BY sld.id
"""

ia_document_pack_acknowledged = """
SELECT
  xn.dp_id importapplicationlicence_id
  , x.user_id
FROM decmgr.xview_notifications xn
  INNER JOIN decmgr.notifications n ON n.id = xn.n_id
  INNER JOIN decmgr.xview_document_packs dp ON dp.dp_id = xn.dp_id
  INNER JOIN impmgr.ima_response_details ird ON ird.ds_id = dp.ds_id
  CROSS JOIN XMLTABLE('/*'
    PASSING n.xml_data
    COLUMNS
      user_id INTEGER PATH '/ACKNOWLEDGEMENT/AUDIT_LIST/AUDIT/ACTION_BY_WUA_ID/text()'
  ) x
WHERE xn.acknowledgement_status = 'ACKNOWLEDGED'
"""

ia_licence_doc_refs = """
SELECT
  'ILD' prefix
  , ir.licence_ref reference_no
  , 'ILD' || ir.licence_ref uref
FROM impmgr.ima_responses ir
WHERE ir.response_type LIKE '%_LICENCE'
"""

ia_licence_max_ref = (
    "SELECT MAX(licence_ref) FROM impmgr.ima_responses WHERE licence_ref IS NOT NULL"
)

ia_timestamp_update = """
UPDATE web_importapplication SET create_datetime = dm_ia.create_datetime, last_update_datetime = dm_ia.last_update_datetime
FROM data_migration_importapplication dm_ia
WHERE web_importapplication.process_ptr_id = dm_ia.id
"""

ia_licence_timestamp_update = """
UPDATE web_importapplicationlicence SET created_at = dm_ial.created_at, updated_at = dm_ial.updated_at
FROM data_migration_importapplicationlicence dm_ial
WHERE web_importapplicationlicence.id = dm_ial.id
"""
