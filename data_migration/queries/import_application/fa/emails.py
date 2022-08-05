__all__ = ["constabulary_emails"]

constabulary_emails = """
SELECT
  ima_id
  , ce.email_status status
  , cd.email_address "to"
  , ce.email_cc_address_list cc_address_list_str
  , ce.email_subject subject
  , ce.email_body body
  , ce.email_response response
  , ce.email_sent_datetime sent_datetime
  , ce.email_closed_datetime closed_datetime
FROM impmgr.xview_ima_constabulary_emails ce
LEFT JOIN impmgr.xview_constabulary_details cd ON cd.con_id = ce.email_constabulary AND cd.status_control = 'C'
WHERE ce.status_control = 'C'
"""
