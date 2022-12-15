__all__ = [
    "users",
    "exporters",
    "importers",
    "mailshots",
    "importer_offices",
    "exporter_offices",
    "access_requests",
]


users = """
WITH login_id_dupes AS (
  SELECT login_id
  FROM securemgr.web_user_accounts wua
  GROUP BY login_id
  HAVING COUNT(id) > 1
)
SELECT
  wuam.wua_id id
  , CASE WHEN ld.login_id IS NOT NULL THEN wuah.login_id || '_' || wuah.wua_id || '_cancelled' ELSE wuah.login_id END username
  , CASE wuah.account_status WHEN 'ACTIVE' THEN 1 ELSE 0 END is_active
  , RAWTOHEX(wuah.encrypt_salt) salt
  , wuah.encrypted_password
  , wuam.last_login_date_time last_login
  , CASE WHEN wuam.wua_id = 0 THEN 'ARCHIVED' ELSE wuah.account_status END account_status
  , wuah.account_status_by account_status_by_id
  , wuah.account_status_date
  , wuah.password_disposition
  , wuah.login_try_count unsuccessful_login_attempts
  , addr.address work_address
  , CASE x.share_info WHEN 'true' THEN 1 ELSE 0 END share_contact_details
  , x.*
FROM securemgr.web_user_account_master wuam
INNER JOIN securemgr.web_user_account_histories wuah ON wuah.wua_id = wuam.wua_id AND wuah.status_control = 'C'
LEFT JOIN login_id_dupes ld ON ld.login_id = wuah.login_id AND wuah.account_status = 'CANCELLED'
INNER JOIN decmgr.resource_people_details rp ON rp.rp_id = wuah.resource_person_id AND (rp.status_control = 'C' OR rp.status = 'DELETE-DRAFT')
CROSS JOIN XMLTABLE('/*'
  PASSING rp.xml_data
  COLUMNS
    title VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/TITLE/text()'
    , first_name VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/FORENAME/text()'
    , preferred_first_name VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/PREFERRED_FORENAME/text()'
    , middle_initials VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/MIDDLE_INITIALS/text()'
    , last_name VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/SURNAME/text()'
    , primary_email_address VARCHAR2(4000) PATH
        '/RESOURCE_PERSON_DETAIL/PERSONAL_EMAIL_LIST/PERSONAL_EMAIL[PORTAL_NOTIFICATIONS/text() = "Primary"]/EMAIL_ADDRESS/text()'
    , date_of_birth VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/DATE_OF_BIRTH/text()'
    , department VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/DEPARTMENT_DESCRIPTION/text()'
    , organisation VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/ORGANISATION_DESCRIPTION/text()'
    , job_title VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/JOB_DESCRIPTION/text()'
    , work_address_id INTEGER PATH '/RESOURCE_PERSON_DETAIL/WORK_ADDRESS_ID/text()'
    , location_at_address VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/LOCATION_AT_ADDRESS/text()'
    , share_info VARCHAR(4000) PATH '/RESOURCE_PERSON_DETAIL/SHARE_ADDRESS_INFO/text()'
    , date_joined_datetime VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/CREATED_DATE/text()'
    , security_question VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/SECURITY_QUESTION/text()'
    , security_answer VARCHAR2(4000) PATH '/RESOURCE_PERSON_DETAIL/SECURITY_ANSWER/text()'
    , email_address_xml XMLTYPE PATH '/RESOURCE_PERSON_DETAIL/PERSONAL_EMAIL_LIST'
    , telephone_xml XMLTYPE PATH '/RESOURCE_PERSON_DETAIL/TELEPHONE_NO_LIST'
) x
LEFT JOIN decmgr.resource_address_current addr ON addr.addr_id = x.work_address_id
ORDER BY wuam.wua_id
"""


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
  , wua_id user_id
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
  , xmd.created_by_wua_id created_by_id
  , xmd.start_datetime create_datetime
  , xmd.published_by_wua published_by_id
  , xmd.published_datetime
  , xmd.retracted_by_wua retracted_by_id
  , xmd.retracted_datetime
  , xmd.version
  , CASE ri.mr_id WHEN 1 THEN 1 ELSE 0 END is_to_importers
  , CASE re.mr_id WHEN 2 THEN 1 ELSE 0 END is_to_exporters
FROM mailshotmgr.mailshots m
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
  , iar.requested_by_wua_id submitted_by_id
  , iar.last_updated_datetime last_update_datetime
  , iar.last_updated_by_wua_id last_updated_by_id
  , iar.closed_datetime
  , iar.closed_by_wua_id closed_by_id
  , CASE WHEN i_org_name IS NULL THEN e_org_name ELSE i_org_name END organisation_name
  , CASE WHEN i_org_address IS NULL THEN e_org_address ELSE i_org_address END organisation_address
  , x.*
FROM impmgr.importer_access_requests iar
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
INNER JOIN securemgr.web_user_accounts wua ON wua.id = iar.requested_by_wua_id
ORDER BY iar.id
"""
