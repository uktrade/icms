# Variations

# TODO ICMSLST-1905 check missing variation requests for specific application types
import_application_variation_count = """
SELECT count(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id
CROSS JOIN XMLTABLE('
for $g1 in /IMA/APP_PROCESSING/VARIATIONS/VARIATION_REQUEST_LIST/VARIATION_REQUEST | <null/>
where /IMA/APP_PROCESSING/VARIATIONS/VARIATION_REQUEST_LIST/VARIATION_REQUEST and $g1/REQUEST_DATE/text()
return
<root>
  <status>{$g1/STATUS/file-id/text()}</status>
</root>
'
PASSING ad.xml_data
COLUMNS
  status VARCHAR2(4000) PATH '/root/status/text()'
) x
WHERE ad.status_control = 'C'
AND ima_type = :IMA_TYPE
AND ima_sub_type = :IMA_SUB_TYPE
"""


# TODO ICMSLST-1905 check variaitons where open/body or open/opened_datetime is null
export_application_variation_count = """
SELECT count(*)
FROM impmgr.xview_certificate_app_details xcad
INNER JOIN impmgr.certificate_app_details cad ON cad.id = xcad.cad_id
CROSS JOIN XMLTABLE('
for $g1 in /CA/CASE/VARIATIONS/VARIATION_LIST/VARIATION | <null/>
where /CA/CASE/VARIATIONS/VARIATION_LIST/VARIATION and $g1/OPEN/BODY/text() and $g1/OPEN/OPENED_DATETIME/text()
return
<root>
  <status>{$g1/STATUS/text()}</status>
</root>
'
PASSING cad.xml_data
COLUMNS
  status VARCHAR2(4000) PATH '/root/status/text()'
) x
WHERE cad.status_control = 'C'
AND xcad.application_type = :CA_TYPE
"""

template_count = """
SELECT COUNT(*)
FROM impmgr.xview_template_details xtd
WHERE xtd.status_control = 'C'
  AND xtd.template_name <> 'Test'
"""

template_country_count = """
SELECT COUNT(*)
FROM impmgr.xview_template_countries xtc
INNER JOIN impmgr.xview_template_details xtd ON xtd.td_id = xtc.td_id
WHERE xtd.status_control = 'C'
  AND xtd.template_name <> 'Test'
"""

cfs_paragraph_count = """
SELECT COUNT(*)
FROM impmgr.xview_template_details xtd
CROSS JOIN XMLTABLE('
for $g1 in /SCHEDULE_BODY/PARAGRAPH
return
<root>
  <name>{$g1/NAME/text()}</name>
  <content>{$g1/VALUE/text()}</content>
</root>
'
PASSING xtd.schedule_body
COLUMNS
  ordinal FOR ordinality
  , name VARCHAR2(4000) PATH '/root/name/text()'
  , content VARCHAR2(4000) PATH '/root/content/text()'
) x
WHERE xtd.status_control = 'C'
  AND xtd.template_type LIKE '%SCHEDULE%'
  AND xtd.template_name <> 'Test'
"""

iat_endorsement_count = """
SELECT COUNT(*)
FROM impmgr.xview_iat_templates iat
WHERE iat.ima_type <> 'GS'
"""

email_address_count = """
SELECT COUNT(*) FROM (
  SELECT
    wuam.wua_id id
    , x.personal_email
  FROM securemgr.web_user_account_master wuam
  INNER JOIN securemgr.web_user_account_histories wuah ON wuah.wua_id = wuam.wua_id AND wuah.status_control = 'C'
  INNER JOIN decmgr.resource_people_details rp ON rp.rp_id = wuah.resource_person_id AND (rp.status_control = 'C' OR rp.status = 'DELETE-DRAFT')
  CROSS JOIN XMLTABLE('
    for $g1 in /RESOURCE_PERSON_DETAIL/PERSONAL_EMAIL_LIST/PERSONAL_EMAIL | <null/>
    where /RESOURCE_PERSON_DETAIL/PERSONAL_EMAIL_LIST/PERSONAL_EMAIL and not($g1/self::null)
    return
    <root>
      <personal_email>{$g1/EMAIL_ADDRESS/text()}</personal_email>
    </root>
  '
  PASSING rp.xml_data
  COLUMNS
    personal_email VARCHAR2(4000) PATH '/root/personal_email/text()'
  ) x
  UNION
  SELECT
    wuam.wua_id id
    , x.personal_email
  FROM securemgr.web_user_account_master wuam
  INNER JOIN securemgr.web_user_account_histories wuah ON wuah.wua_id = wuam.wua_id AND wuah.status_control = 'C'
  INNER JOIN decmgr.resource_people_details rp ON rp.rp_id = wuah.resource_person_id AND (rp.status_control = 'C' OR rp.status = 'DELETE-DRAFT')
  CROSS JOIN XMLTABLE('
    for $g1 in /RESOURCE_PERSON_DETAIL/DISTRIBUTION_EMAIL_LIST/DISTRIBUTION_EMAIL | <null/>
    where /RESOURCE_PERSON_DETAIL/DISTRIBUTION_EMAIL_LIST/DISTRIBUTION_EMAIL and not($g1/self::null)
    return
    <root>
      <personal_email>{$g1/EMAIL_ADDRESS/text()}</personal_email>
    </root>
  '
  PASSING rp.xml_data
  COLUMNS
    personal_email VARCHAR2(4000) PATH '/root/personal_email/text()'
  ) x
)
"""

withdrawal_export_application_count = """
SELECT COUNT(*) FROM impmgr.xview_cert_app_withdrawals xcaw
WHERE withdrawal_status <> 'DRAFT' AND status_control = 'C'
"""

withdrawal_import_application_count = """
SELECT COUNT(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id
CROSS JOIN XMLTABLE('for $g1 in /IMA/APP_PROCESSING/WITHDRAWAL/WITHDRAW_LIST/WITHDRAW | <null/>
where /IMA/APP_PROCESSING/WITHDRAWAL/WITHDRAW_LIST/WITHDRAW and $g1/WITHDRAW_STATUS/text()
return
<root>
  <status>{$g1/WITHDRAW_STATUS/text()}</status>
</root>
'
PASSING ad.xml_data
COLUMNS
  status VARCHAR2(4000) PATH '/root/status/text()'
) x
WHERE ad.status_control = 'C'
AND x.status <> 'DRAFT'
"""

sanctions_email_count = """
SELECT COUNT(*)
FROM impmgr.saction_email_details
WHERE sanction_email_id <> 1
AND status_control = 'C'
"""

export_certificate_draft_count = """
SELECT COUNT(*)
FROM impmgr.certificate_app_responses car
  INNER JOIN impmgr.cert_app_response_details card ON card.car_id = car.id
WHERE card.status = 'DRAFT'
"""

export_certificate_revoked_count = """
SELECT COUNT(*)
FROM impmgr.certificate_app_responses car
  INNER JOIN impmgr.cert_app_response_details card ON card.car_id = car.id
  INNER JOIN impmgr.certificate_applications ca ON ca.id = car.ca_id
  INNER JOIN impmgr.certificate_app_details cad_c ON cad_c.ca_id = car.ca_id AND cad_c.status_control = 'C'
WHERE cad_c.status = 'REVOKED'
"""

export_certificate_active_count = """
SELECT COUNT(*)
FROM impmgr.certificate_app_responses car
  INNER JOIN impmgr.cert_app_response_details card ON card.car_id = car.id
  INNER JOIN impmgr.certificate_applications ca ON ca.id = car.ca_id
  INNER JOIN impmgr.certificate_app_details cad_c ON cad_c.ca_id = car.ca_id AND cad_c.status_control = 'C'
WHERE cad_c.status <> 'REVOKED' and card.is_last_issued <> 'false' and card.status <> 'DRAFT'
"""
