# The xview_ima_constabulary_emails view truncates the body and response over 4000 characters so extract those fields from the xml
constabulary_emails = """
SELECT
  ce.ima_id
  , ce.email_status status
  , cd.email_address "to"
  , ce.email_cc_address_list cc_address_list_str
  , ce.email_subject subject
  , x.body
  , x.response
  , ce.email_sent_datetime sent_datetime
  , ce.email_closed_datetime closed_datetime
  , firearms_certificate_list constabulary_attachments_xml
  , 'IMA_CONSTAB_EMAIL' template_code
  , 'CONSTABULARY' email_type
FROM impmgr.xview_ima_constabulary_emails ce
INNER JOIN impmgr.import_application_details iad ON iad.ima_id = ce.ima_id AND iad.status_control = 'C'
CROSS JOIN XMLTABLE('/*/APP_PROCESSING/CONSTABULARY_EMAIL_MASTER/CONSTABULARY_EMAIL_LIST/CONSTABULARY_EMAIL'
  PASSING iad.xml_data
  COLUMNS
  body CLOB PATH '/*/EMAIL_BODY/text()'
  , response CLOB PATH '/*/EMAIL_RESPONSE/text()'
) x
LEFT JOIN impmgr.xview_constabulary_details cd ON cd.con_id = ce.email_constabulary AND cd.status_control = 'C'
WHERE iad.status_control = 'C'
ORDER BY ima_id
"""
