constabulary_emails = """
SELECT
  iad.id imad_id
  , iad.ima_id
  , x.status email_status
  , cd.email_address "to"
  , x.email_cc_address_list cc_address_list_str
  , x.email_subject subject
  , x.firearms_certificate_list constabulary_attachments_xml
  , email_body body
  , x.email_response response
  , dt.to_date_safe(x.sent_datetime, 'YYYY-MM-DD"T"HH24:MI:SS') sent_datetime
  , dt.to_date_safe(x.closed_datetime, 'YYYY-MM-DD"T"HH24:MI:SS') closed_datetime
FROM impmgr.import_application_details iad
CROSS JOIN XMLTABLE('/*/APP_PROCESSING/CONSTABULARY_EMAIL_MASTER/CONSTABULARY_EMAIL_LIST/CONSTABULARY_EMAIL'
  PASSING iad.xml_data
  COLUMNS
    status VARCHAR2(4000) PATH '/*/STATUS/text()'
  , constabulary VARCHAR2(4000) PATH '/*/CONSTABULARY/text()'
  , email_cc_address_list VARCHAR2(4000) PATH '/*/EMAIL_CC_ADDRESS_LIST/text()'
  , email_subject VARCHAR2(4000) PATH '/*/EMAIL_SUBJECT/text()'
  , firearms_certificate_list XMLTYPE PATH '/*/FIREARMS_CERTIFICATE_LIST'
  , email_body CLOB PATH '/*/EMAIL_BODY/text()'
  , email_response CLOB PATH '/*/EMAIL_RESPONSE/text()'
  , sent_datetime VARCHAR2(4000) PATH '/*/SENT_DATETIME/text()'
  , closed_datetime VARCHAR2(4000) PATH '/*/CLOSED_DATETIME/text()'
) x
LEFT JOIN impmgr.xview_constabulary_details cd ON cd.con_id = x.constabulary AND cd.status_control = 'C'
WHERE iad.status_control = 'C'
"""
