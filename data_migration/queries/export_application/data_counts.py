# Certifcates of Free Sale

cfs_product_count = """
SELECT count(*)
FROM impmgr.xview_certificate_app_details xcad
INNER JOIN impmgr.certificate_app_details cad ON cad.id = xcad.cad_id
CROSS JOIN XMLTABLE('
for $g1 in /CA/APPLICATION/PRODUCTS/SCHEDULE_LIST/SCHEDULE | <null/>
where /CA/APPLICATION/PRODUCTS/SCHEDULE_LIST/SCHEDULE and not($g1/self::null)
return
for $g2 in $g1/PRODUCT_LIST/PRODUCT | <null/>
where $g1/PRODUCT_LIST/PRODUCT and $g2/NAME/text()
return
<root>
  <name>{$g2/NAME/text()}</name>
</root>
'
PASSING cad.xml_data
COLUMNS
  name VARCHAR2(4000) PATH '/root/name/text()'
) x
WHERE xcad.status_control = 'C'
  AND xcad.application_type = 'CFS'
  AND xcad.status <> 'DELETED'
  AND (xcad.status <> 'IN_PROGRESS' OR xcad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""

cfs_product_active_ingredient_count = """
SELECT count(*)
FROM impmgr.xview_certificate_app_details xcad
INNER JOIN impmgr.certificate_app_details cad ON cad.id = xcad.cad_id
CROSS JOIN XMLTABLE('
for $g1 in /CA/APPLICATION/PRODUCTS/SCHEDULE_LIST/SCHEDULE | <null/>
where /CA/APPLICATION/PRODUCTS/SCHEDULE_LIST/SCHEDULE and not($g1/self::null)
return
for $g2 in $g1/PRODUCT_LIST/PRODUCT | <null/>
where $g1/PRODUCT_LIST/PRODUCT and $g2/NAME/text()
return
for $g3 in $g2/ACTIVE_INGREDIENT_LIST/ACTIVE_INGREDIENT | <null/>
where $g2/ACTIVE_INGREDIENT_LIST/ACTIVE_INGREDIENT and $g3/NAME/text() and $g3/CAS_NUMBER/text()
return
<root>
  <name>{$g3/NAME/text()}</name>
</root>
'
PASSING cad.xml_data
COLUMNS
  name VARCHAR2(4000) PATH '/root/name/text()'
) x
WHERE xcad.status_control = 'C'
  AND xcad.application_type = 'CFS'
  AND xcad.status <> 'DELETED'
  AND (xcad.status <> 'IN_PROGRESS' OR xcad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""

cfs_product_type_numbers_count = """
SELECT count(*)
FROM impmgr.xview_certificate_app_details xcad
INNER JOIN impmgr.certificate_app_details cad ON cad.id = xcad.cad_id
CROSS JOIN XMLTABLE('
for $g1 in /CA/APPLICATION/PRODUCTS/SCHEDULE_LIST/SCHEDULE | <null/>
where /CA/APPLICATION/PRODUCTS/SCHEDULE_LIST/SCHEDULE and not($g1/self::null)
return
for $g2 in $g1/PRODUCT_LIST/PRODUCT | <null/>
where $g1/PRODUCT_LIST/PRODUCT and $g2/NAME/text()
return
for $g3 in $g2/PRODUCT_TYPE_NUMBER_LIST/PRODUCT_TYPE_NUMBER | <null/>
where $g2/PRODUCT_TYPE_NUMBER_LIST/PRODUCT_TYPE_NUMBER and $g3/NUMBER/text()
return
<root>
  <pt_number>{$g3/NUMBER/text()}</pt_number>
</root>
'
PASSING cad.xml_data
COLUMNS
  pt_number INTEGER PATH '/root/pt_number/text()'
) x
WHERE xcad.status_control = 'C'
  AND xcad.application_type = 'CFS'
  AND xcad.status <> 'DELETED'
  AND (xcad.status <> 'IN_PROGRESS' OR xcad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""

cfs_schedule_legislation_count = """
SELECT count(*)
FROM impmgr.xview_certificate_app_details xcad
INNER JOIN impmgr.certificate_app_details cad ON cad.id = xcad.cad_id
CROSS JOIN XMLTABLE('
for $g1 in /CA/APPLICATION/PRODUCTS/SCHEDULE_LIST/SCHEDULE | <null/>
where /CA/APPLICATION/PRODUCTS/SCHEDULE_LIST/SCHEDULE and not($g1/self::null)
return
for $g2 in $g1/LEGISLATION_LIST/LEGISLATION | <null/>
where $g1/LEGISLATION_LIST/LEGISLATION and $g2/text()
return
<root>
  <legislation>{$g2/text()}</legislation>
</root>
'
PASSING cad.xml_data
COLUMNS
  legislation VARCHAR2(4000) PATH '/root/legislation/text()'
) x
WHERE xcad.status_control = 'C'
  AND xcad.application_type = 'CFS'
  AND xcad.status <> 'DELETED'
  AND (xcad.status <> 'IN_PROGRESS' OR xcad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""

export_application_case_notes_count = """
SELECT count(*)
FROM impmgr.xview_certificate_app_details xcad
INNER JOIN impmgr.certificate_app_details cad ON cad.id = xcad.cad_id
CROSS JOIN XMLTABLE('
for $g1 in /CA/CASE/NOTES/NOTE_LIST/NOTE | <null/>
where /CA/CASE/NOTES/NOTE_LIST/NOTE and not($g1/self::null)
return
<root>
  <note_id>{$g1/NOTE_ID/text()}</note_id>
</root>
'
PASSING cad.xml_data
COLUMNS
  note_id VARCHAR2(4000) PATH '/root/note_id/text()'
) x
WHERE xcad.status_control = 'C'
"""
