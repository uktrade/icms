template = """
SELECT
  xtd.t_id id
  , CASE xtd.template_status WHEN 'ACTIVE' THEN 1 ELSE 0 END is_active
  , xtd.template_name
  , xtd.template_mnem template_code
  , xtd.template_type
  , xtd.application_domain
  , ctry_translation_set_id country_translation_set_id
FROM impmgr.xview_template_details xtd
  INNER JOIN impmgr.template_details td ON td.id = xtd.td_id
WHERE xtd.status_control = 'C'
  AND xtd.template_name <> 'Test'
ORDER BY xtd.t_id
"""


template_version = """
SELECT
  xtd.t_id template_id
  , td.start_datetime
  , td.end_datetime
  , CASE xtd.status_control WHEN 'C' THEN 1 ELSE 0 END is_active
  , xtd.template_type
  , CASE
    WHEN xtd.template_type = 'EMAIL_TEMPLATE' THEN xtd.email_subject
    ELSE xtd.declaration_title
  END title
  , CASE
    WHEN xtd.template_type LIKE 'LETTER_%' THEN xtd.letter_body
    WHEN xtd.template_type = 'DECLARATION' THEN TO_CLOB(xtd.declaration_text)
    WHEN xtd.template_type = 'ENDORSEMENT' THEN TO_CLOB(xtd.endorsement_text)
    WHEN xtd.template_type = 'EMAIL_TEMPLATE' THEN TO_CLOB(xtd.email_body)
    WHEN xtd.template_type = 'CFS_DECLARATION_TRANSLATION' THEN TO_CLOB(EXTRACT(xtd.translation_body, '/TRANSLATION_BODY/*'))
  END content
  , xtd.version_no version_number
  , td.created_by_wua_id created_by_id
FROM impmgr.xview_template_details xtd
  INNER JOIN impmgr.template_details td ON td.id = xtd.td_id
WHERE xtd.template_name <> 'Test'
ORDER BY xtd.t_id
"""


template_country = """
SELECT
  xtc.t_id template_id
  , xtc.country_id
FROM impmgr.xview_template_countries xtc
INNER JOIN impmgr.xview_template_details xtd ON xtd.td_id = xtc.td_id
WHERE xtd.status_control = 'C'
  AND xtd.template_name <> 'Test'
ORDER BY 1, 2
"""

cfs_paragraph = """
SELECT
  xtd.t_id template_id
  , x.*
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
ORDER BY xtd.t_id
"""

endorsement_template = """
SELECT iat_id importapplicationtype_id, template_id
FROM impmgr.xview_iat_templates iat
WHERE ima_type <> 'GS'
"""

template_version_timestamp_update = """
UPDATE web_templateversion SET start_datetime = dm_tv.start_datetime
FROM data_migration_templateversion dm_tv
WHERE web_templateversion.id = dm_tv.id
"""
