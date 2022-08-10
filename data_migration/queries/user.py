__all__ = ["importers", "mailshots", "offices"]

# After users migrated
# , wua_id user_id

importers = """
SELECT
  imp_id id
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , imp_entity_type type
  , organisation_name name
  , reg_number registered_number
  , eori_number
  , 2 user_id
  , main_imp_id main_importer_id
  , other_coo_code region_origin
FROM impmgr.xview_importer_details xid
WHERE status_control = 'C'
ORDER BY imp_id
"""


offices = """
SELECT
  rownum id
  , imp_id importer_id
  , imp_id || '-' || office_id legacy_id
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , postcode
  , address
  , eori_number
  , address_entry_type
FROM impmgr.xview_importer_offices xio
WHERE status_control = 'C'
ORDER BY imp_id, office_id
"""


mailshots = """
SELECT
  xmd.documents_ff_id folder_id
  , m.reference
  , xmd.status
  , xmd.subject title
  , xmd.description
  , xmd.publish_email_subject email_subject
  , xmd.publish_email_body email_body
  , CASE xmd.SEND_RETRACT_EMAILS WHEN 'true' THEN 1 ELSE 0 END is_retraction_email
  , xmd.retract_email_subject
  , xmd.retract_email_body
  , 2 created_by_id
  , xmd.start_datetime create_datetime
  , CASE xmd.published_by_wua WHEN NULL THEN NULL ELSE 2 END published_by_id
  , xmd.published_datetime
  , CASE xmd.retracted_by_wua WHEN NULL THEN NULL ELSE 2 END retracted_by_id
  , xmd.retracted_datetime
  , xmd.version
  , CASE ri.mr_id WHEN 1 THEN 1 ELSE 0 END is_to_importers
  , CASE re.mr_id WHEN 2 THEN 1 ELSE 0 END is_to_exporters
FROM MAILSHOTMGR.mailshots m
INNER JOIN mailshotmgr.xview_mailshot_details xmd ON xmd.M_ID = m.id
LEFT JOIN mailshotmgr.xview_mailshot_selected_rcpts ri ON ri.m_id = xmd.m_id AND ri.mr_id = 1
LEFT JOIN mailshotmgr.xview_mailshot_selected_rcpts re ON re.m_id = xmd.m_id AND re.mr_id = 2
WHERE xmd.status_control = 'C'
ORDER BY m.id
"""
