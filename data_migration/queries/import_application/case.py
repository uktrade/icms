__all__ = ["case_note", "fir", "update_request"]

case_note = """
SELECT
  xid.ima_id, cnd.*
FROM impmgr.case_notes cn
INNER JOIN (
  SELECT cn_id, status, 2 created_by_id, x.*
  FROM impmgr.case_note_details cnd,
    XMLTABLE('/*'
    PASSING xml_data
    COLUMNS
      note CLOB PATH '/CASE_NOTE_DATA/REQUEST_BODY/text()'
      , create_datetime VARCHAR(30) PATH '/CASE_NOTE_DATA/CREATED_DATETIME/text()'
      , file_folder_id INTEGER PATH '/CASE_NOTE_DATA/FILE_FOLDER_ID/text()'
  ) x
  WHERE status_control = 'C'
) cnd ON cnd.cn_id = cn.id
INNER JOIN impmgr.xview_ima_details xid ON xid.ima_id = cn.ima_id AND xid.status_control = 'C'
"""


update_request = """
SELECT
  u.ima_id
  , update_status status
  , request_subject
  , request_body request_detail
  , response_details
  , request_date request_datetime
  , 2 request_by_id
  , response_date response_datetime
  , 2 response_by_id
  , closed_date closed_datetime
  , 2 closed_by_id
FROM impmgr.xview_ima_updates u
INNER JOIN impmgr.xview_ima_details xid ON xid.ima_id = u.ima_id AND xid.status_control = 'C'
"""


fir = """
SELECT
  xir.ima_id ia_ima_id
  , rfi_status status
  , request_subject
  , request_body request_detail
  , request_cc_email_list email_cc_address_list_str
  , request_date requested_datetime
  , response_details response_detail
  , response_date response_datetime
  , 2 requested_by_id
  , 2 response_by_id
  , closed_date closed_datetime
  , 2 closed_by_id
  , deleted_date deleted_datetime
  , 2 deleted_by_id
  , 'FurtherInformationRequest' process_type
  , file_folder_id folder_id
FROM impmgr.xview_ima_rfis xir
INNER JOIN impmgr.xview_ima_details xid ON xid.ima_id = xir.ima_id AND xid.status_control = 'C'
WHERE xir.status_control = 'C'
"""
