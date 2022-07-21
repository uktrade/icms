__all__ = ["ia_licence", "ia_licence_docs"]

# TODO: Look at statuses again

ia_licence = """
SELECT
  ird.imad_id
  , ird.licence_start_date
  , ird.licence_end_date
  , ia.case_ref case_reference
  , xiad.print_documents_flag is_paper_only
  , ird.id legacy_id
  , CASE
      WHEN xiad.status IN ('REVOKED', 'WITHDRAWN', 'STOPPED') THEN 'AR'
      WHEN ird.licence_validity IS NULL THEN 'AR'
      WHEN xiad.status IN ('PROCESSING', 'VARIATION_REQUESTED', 'SUBMITTED') THEN 'DR'
      WHEN iad.case_closed_datetime IS NOT NULL THEN 'AC'
      ELSE 'AC'
  END status
  , ir.created_datetime created_at
  , iad.case_closed_datetime case_completion_date
FROM impmgr.ima_responses ir
  INNER JOIN impmgr.ima_response_details ird ON ird.ir_id = ir.id
  INNER JOIN impmgr.xview_ima_details xiad ON xiad.imad_id = ird.imad_id
  INNER JOIN impmgr.import_applications ia ON ia.id = xiad.ima_id
  INNER JOIN impmgr.import_application_details iad ON iad.id = xiad.imad_id
WHERE ir.response_type LIKE '%_LICENCE'
AND xiad.status_control = 'C'
"""

#  , dd.signed_datetime
#  , CASE WHEN dd.signed_by_id IS NULL THEN NULL ELSE 2 END signed_by_id

ia_licence_docs = """
SELECT
  ird.id licence_id
  , ir.licence_ref || ir.licence_check_letter reference
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
  INNER JOIN impmgr.xview_ima_rd_di_details xird ON xird.ir_id = ir.id
  INNER JOIN decmgr.xview_document_data xdd ON xdd.di_id = xird.di_id AND xdd.system_document = 'N' AND xdd.content_description = 'PDF'
  INNER JOIN decmgr.document_data dd ON dd.id = xdd.dd_id
  INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(dd.secure_lob_ref).id
WHERE ir.response_type LIKE '%_LICENCE'
AND xiad.status_control = 'C'
"""
