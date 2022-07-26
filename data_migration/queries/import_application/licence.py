__all__ = ["ia_licence", "ia_licence_docs"]

# TODO: Look at statuses again

ia_licence = """
SELECT
  ir.ima_id
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
  , ird.start_datetime case_completion_date
FROM impmgr.ima_responses ir
  INNER JOIN impmgr.ima_response_details ird ON ird.ir_id = ir.id
  INNER JOIN impmgr.xview_ima_details xiad ON xiad.imad_id = ird.imad_id
  INNER JOIN impmgr.import_applications ia ON ia.id = xiad.ima_id
WHERE ir.response_type LIKE '%_LICENCE'
ORDER BY ir.ima_id, ird.variation_no
"""

#  , dd.signed_datetime
#  , CASE WHEN dd.signed_by_id IS NULL THEN NULL ELSE 2 END signed_by_id

ia_licence_docs = """
SELECT
  ird.id licence_id
  , CASE
    WHEN xiad.print_documents_flag = 'Y' THEN ''
    WHEN xiad.ima_sub_type = 'OIL' THEN 'GBOIL'
    WHEN xiad.ima_type = 'FA' THEN 'GBSIL'
    WHEN xiad.ima_type = 'SPS' THEN 'GBAOG'
    WHEN xiad.ima_type = 'TEX' THEN 'GBTEX'
    WHEN xiad.ima_type = 'SAN' THEN 'GBSAN'
    WHEN xiad.ima_type = 'ADHOC' THEN 'GBSAN'
  END || ir.licence_ref || ir.licence_check_letter reference
  , dd.id document_legacy_id
  , 'LICENCE' document_type
  , xdd.title filename
  , xdd.content_type
  , dbms_lob.getlength(sld.blob_data) file_size
  , sld.id || '-' || xdd.title path
  , dd.created_datetime
  , 2 created_by_id
FROM impmgr.ima_responses ir
  INNER JOIN impmgr.ima_response_details ird ON ird.ir_id = ir.id
  INNER JOIN impmgr.xview_ima_details xiad ON xiad.imad_id = ird.imad_id
  INNER JOIN impmgr.xview_ima_rd_di_details xird ON xird.ird_id = ird.id
  INNER JOIN decmgr.xview_document_data xdd ON xdd.di_id = xird.di_id AND xdd.system_document = 'N' AND xdd.content_description = 'PDF'
  INNER JOIN decmgr.document_data dd ON dd.id = xdd.dd_id
  INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(dd.secure_lob_ref).id
WHERE ir.response_type LIKE '%_LICENCE'
ORDER BY ir.id, dd.id
"""
