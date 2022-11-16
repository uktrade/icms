__all__ = [
    "exporters",
    "importers",
    "mailshots",
    "importer_offices",
    "exporter_offices",
    "access_requests",
]

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


importer_offices = """
SELECT
  imp_id importer_id
  , 'i-' || imp_id || '-' || office_id legacy_id
  , CASE office_status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , postcode
  , address
  , eori_number
  , address_entry_type
FROM impmgr.xview_importer_offices xio
WHERE status_control = 'C'
ORDER BY imp_id, office_id
"""


exporters = """
SELECT
  e.id
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , organisation_name name
  , organisation_registered_number registered_number
  , comments
  , e.main_e_id main_exporter_id
FROM impmgr.exporters e
INNER JOIN impmgr.xview_exporter_details xed ON xed.e_id = e.id
WHERE status_control = 'C'
ORDER BY e.id
"""


exporter_offices = """
SELECT
  e_id exporter_id
  , 'e-' || e_id || '-' || office_id legacy_id
  , CASE office_status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , postcode
  , address
  , address_entry_type
FROM impmgr.xview_exporter_offices xio
WHERE status_control = 'C'
ORDER BY e_id, office_id
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


access_requests = """
SELECT
  iar.id iar_id
  , CASE
    WHEN iar.request_type IN ('MAIN_IMPORTER_ACCESS', 'AGENT_IMPORTER_ACCESS')
    THEN 'ImporterAccessRequest'
    ELSE 'ExporterAccessRequest'
  END process_type
  , iar.request_reference reference
  , iar.status
  , iar.request_type
  , iar.requested_datetime submit_datetime
  , 2 submitted_by_id
  , iar.last_updated_datetime last_update_datetime
  , 2 last_updated_by_id
  , iar.closed_datetime
  , 2 closed_by_id
  , CASE WHEN i_org_name IS NULL THEN e_org_name ELSE i_org_name END organisation_name
  , CASE WHEN i_org_address IS NULL THEN e_org_address ELSE i_org_address END organisation_address
  , x.*
FROM IMPMGR.IMPORTER_ACCESS_REQUESTS iar
CROSS JOIN XMLTABLE('/*'
  PASSING iar.xml_data
  COLUMNS
    i_org_name VARCHAR2(4000) PATH '/IMPORTER_ACCESS_REQUEST/NEW_REQUEST/IMPORTER/NAME/text()'
    , i_org_address VARCHAR2(4000) PATH '/IMPORTER_ACCESS_REQUEST/NEW_REQUEST/IMPORTER/ADDRESS/text()'
    , e_org_name VARCHAR2(4000) PATH '/IMPORTER_ACCESS_REQUEST/NEW_REQUEST/EXPORTER/NAME/text()'
    , e_org_address VARCHAR2(4000) PATH '/IMPORTER_ACCESS_REQUEST/NEW_REQUEST/EXPORTER/ADDRESS/text()'
    , request_reason VARCHAR2(4000) PATH '/IMPORTER_ACCESS_REQUEST/NEW_REQUEST/IMPORTER/REASON_FOR_REQUEST/text()'
    , agent_name VARCHAR2(4000) PATH '/IMPORTER_ACCESS_REQUEST/NEW_REQUEST/AGENT/NAME/text()'
    , agent_address VARCHAR2(4000) PATH '/IMPORTER_ACCESS_REQUEST/NEW_REQUEST/AGENT/ADDRESS/text()'
    , response VARCHAR(4000) PATH '/IMPORTER_ACCESS_REQUEST/CLOSE_REQUEST/RESPONSE/text()'
    , response_reason VARCHAR(4000) PATH '/IMPORTER_ACCESS_REQUEST/CLOSE_REQUEST/RESPONSE_REASON/text()'
    , importer_id INTEGER PATH '/IMPORTER_ACCESS_REQUEST/NEW_REQUEST/IMPORTER/LINK/IMP_ID/text()'
    , exporter_id INTEGER PATH '/IMPORTER_ACCESS_REQUEST/NEW_REQUEST/EXPORTER/LINK/E_ID/text()'
    , fir_xml XMLTYPE PATH '/IMPORTER_ACCESS_REQUEST/RFIS/RFI_LIST'
    , approval_xml XMLTYPE PATH '/IMPORTER_ACCESS_REQUEST/REQUEST_APPROVAL'
) x
ORDER BY iar.id
"""
