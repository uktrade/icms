case_note = """
SELECT
  xid.ima_id, cnd.status, cnd.created_by_wua_id created_by_id, x.*
FROM impmgr.case_notes cn
INNER JOIN impmgr.xview_ima_details xid ON xid.ima_id = cn.ima_id AND xid.status_control = 'C'
INNER JOIN impmgr.case_note_details cnd ON cnd.cn_id = cn.id AND cnd.status_control = 'C'
CROSS JOIN XMLTABLE('/*'
  PASSING xml_data
  COLUMNS
    note CLOB PATH '/CASE_NOTE_DATA/REQUEST_BODY/text()'
    , create_datetime VARCHAR(30) PATH '/CASE_NOTE_DATA/CREATED_DATETIME/text()'
    , file_folder_id INTEGER PATH '/CASE_NOTE_DATA/FILE_FOLDER_ID/text()'
) x
"""


update_request = """
SELECT
  u.ima_id
  , update_status status
  , request_subject
  , request_body request_detail
  , response_details response_detail
  , request_date request_datetime
  , u.request_by_wua_id requested_by_id
  , response_date response_datetime
  , u.response_by_wua_id response_by_id
  , closed_date closed_datetime
  , u.closed_by_wua_id closed_by_id
FROM impmgr.xview_ima_updates u
INNER JOIN impmgr.xview_ima_details xid ON xid.ima_id = u.ima_id AND xid.status_control = 'C'
WHERE u.status_control = 'C'
"""


fir = """
SELECT
  xir.ima_id ia_ima_id
  , CASE rfi_status WHEN 'DELETED' THEN 0 ELSE 1 END is_active
  , rfi_status status
  , request_date created
  , request_subject
  , request_body request_detail
  , request_cc_email_list email_cc_address_list_str
  , request_date requested_datetime
  , response_details response_detail
  , response_date response_datetime
  , xir.request_by_wua_id requested_by_id
  , xir.response_by_wua_id response_by_id
  , closed_date closed_datetime
  , xir.closed_by_wua_id closed_by_id
  , deleted_date deleted_datetime
  , xir.deleted_by_wua_id deleted_by_id
  , 'FurtherInformationRequest' process_type
  , file_folder_id folder_id
FROM impmgr.xview_ima_rfis xir
INNER JOIN impmgr.xview_ima_details xid ON xid.ima_id = xir.ima_id AND xid.status_control = 'C'
WHERE xir.status_control = 'C'
AND xir.request_date IS NOT NULL
"""


endorsement = """
SELECT imad_id, endorsement_text content
FROM impmgr.xview_ima_endorsements xie
WHERE xie.status_control = 'C'
AND endorsement_text IS NOT NULL
"""


sigl_transmission = """
SELECT
  ima_id
  , status
  , trans_type transmission_type
  , request_type
  , created_by_wua_id sent_by_id
  , created_datetime sent_datetime
  , response_datetime
  , response_code
  , response_msg response_message
FROM impmgr.sigl_transmissions
"""


# Case note has no updated timestamp in V1 so use created

case_note_created_timestamp_update = """
UPDATE web_casenote SET create_datetime = data_migration_casenote.create_datetime, updated_at = data_migration_casenote.create_datetime
FROM data_migration_casenote
WHERE web_casenote.id = data_migration_casenote.id
"""


fir_timestamp_update = """
UPDATE web_furtherinformationrequest SET requested_datetime = data_migration_furtherinformationrequest.requested_datetime
FROM data_migration_furtherinformationrequest
WHERE web_furtherinformationrequest.process_ptr_id = data_migration_furtherinformationrequest.id
"""


process_timestamp_update = """
UPDATE web_process SET created = data_migration_process.created
FROM data_migration_process
WHERE web_process.id = data_migration_process.id
"""


export_process_order_datetime_update = """
UPDATE web_process SET order_datetime = dm_ea.last_update_datetime
FROM data_migration_exportapplication dm_ea
WHERE web_process.id = dm_ea.id
"""


import_process_order_datetime_update = """
UPDATE web_process SET order_datetime = dm_ia.last_update_datetime
FROM data_migration_importapplication dm_ia
WHERE web_process.id = dm_ia.id
"""


access_request_process_order_datetime_update = """
UPDATE web_process SET order_datetime = dm_ar.last_update_datetime
FROM data_migration_accessrequest dm_ar
WHERE web_process.id = dm_ar.id
"""


variation_request_timestamp_update = """
UPDATE web_variationrequest SET requested_datetime = data_migration_variationrequest.requested_datetime
FROM data_migration_variationrequest
WHERE web_variationrequest.id = data_migration_variationrequest.id
"""


withdraw_application_timestamp_update = """
UPDATE web_withdrawapplication
SET created_datetime = data_migration_withdrawapplication.created_datetime
  , updated_datetime = data_migration_withdrawapplication.updated_datetime
FROM data_migration_withdrawapplication
WHERE web_withdrawapplication.id = data_migration_withdrawapplication.id
"""
