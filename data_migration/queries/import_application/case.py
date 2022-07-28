__all__ = ["case_note"]

case_note = """
SELECT
  xid.imad_id, cnd.*
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
