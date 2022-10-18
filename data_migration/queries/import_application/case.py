__all__ = ["case_note", "endorsement", "fir", "update_request", "import_workbasket"]

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
  , CASE rfi_status WHEN 'DELETED' THEN 0 ELSE 1 END is_active
  , rfi_status status
  , request_date created
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


endorsement = """
SELECT imad_id, endorsement_text content
FROM impmgr.xview_ima_endorsements xie
WHERE xie.status_control = 'C'
"""


import_workbasket = """
SELECT
  u.ima_id
  , CASE xwa.terminated_flag WHEN 'N' THEN 1 ELSE 0 END is_active
  , xwa.action_mnem
  , xwa.action_desc action_description
  , xwa.start_datetime
  , xwa.end_datetime
FROM bpmmgr.xview_workbasket_actions xwa
INNER JOIN bpmmgr.urefs u ON u.uref = xwa.primary_data_uref AND u.ima_id IS NOT NULL
INNER JOIN impmgr.xview_ima_details xiad ON xiad.ima_id = u.ima_id AND xiad.status_control = 'C'
INNER JOIN impmgr.import_application_types iat
  ON iat.ima_type = xiad.ima_type AND iat.ima_sub_type = xiad.ima_sub_type
WHERE xwa.terminated_flag = 'N'
  AND xwa.action_mnem NOT IN (
    'ii.H40.ACKNOWLEDGE', '1.IMA30.IMP_IMA', '1.IMA35.IMP_IMA',
    'i.H2.ACKNOWLEDGE', 'i.H21.ACKNOWLEDGE', '1.IMA33.IMP_IMA'
  )
  AND xiad.status <> 'DELETED'
  AND (
    (iat.status = 'ARCHIVED' AND xiad.submitted_datetime IS NOT NULL)
    OR (
      iat.status = 'CURRENT' AND (
        xiad.submitted_datetime IS NOT NULL OR xiad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY
      )
    )
  )
ORDER BY xwa.wba_id
"""
