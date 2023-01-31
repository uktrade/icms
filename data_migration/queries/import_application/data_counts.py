# Firearms and Ammunition Goods and Certificates

# TODO: Check OIL applications where targe_id is null or certificate_type is null

fa_goods_certificate_count = """
SELECT count(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = :FA_TYPE
CROSS JOIN XMLTABLE('
for $g1 in /IMA/APP_DETAILS/FA_DETAILS/FIREARMS_CERTIFICATE_LIST/FIREARMS_CERTIFICATE | <null/>
where /IMA/APP_DETAILS/FA_DETAILS/FIREARMS_CERTIFICATE_LIST/FIREARMS_CERTIFICATE and $g1/TARGET_ID/text() and $g1/CERTIFICATE_TYPE/text()
return
<root>
  <certificate_ref>{$g1/CERTIFICATE_REF/text()}</certificate_ref>
</root>
'
PASSING ad.xml_data
COLUMNS
  certificate_ref VARCHAR(4000) PATH '/root/certificate_ref/text()'
) x
WHERE ad.status_control = 'C'
AND x.certificate_ref IS NOT NULL
AND (xid.submitted_datetime IS NOT NULL OR xid.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""

sil_section_goods_count = """
SELECT count(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = 'SIL'
CROSS JOIN XMLTABLE('
for $g1 in /IMA/APP_DETAILS/FA_DETAILS/COMMODITY_LIST/COMMODITY | <null/>
where /IMA/APP_DETAILS/FA_DETAILS/COMMODITY_LIST/COMMODITY and $g1/SECTION/text()
return
<root>
  <commodity_desc>{$g1/COMMODITY_DESC/text()}</commodity_desc>
  <sec>{$g1/SECTION/text()}</sec>
</root>
'
PASSING ad.xml_data
COLUMNS
  commodity_desc VARCHAR(4000) PATH '/root/commodity_desc/text()'
  , sec VARCHAR(20) PATH '/root/sec/text()'
) x
WHERE ad.status_control = 'C'
AND x.commodity_desc IS NOT NULL
AND x.sec = :SECTION
AND (xid.submitted_datetime IS NOT NULL OR xid.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""

sil_legacy_goods_count = """
SELECT count(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = 'SIL'
CROSS JOIN XMLTABLE('
for $g1 in /IMA/APP_DETAILS/FA_DETAILS/COMMODITY_LIST/COMMODITY | <null/>
where /IMA/APP_DETAILS/FA_DETAILS/COMMODITY_LIST/COMMODITY and not($g1/self::null) and not($g1/SECTION/text())
return
<root>
  <commodity_desc>{$g1/COMMODITY_DESC/text()}</commodity_desc>
</root>
'
PASSING ad.xml_data
COLUMNS
  commodity_desc VARCHAR(4000) PATH '/root/commodity_desc/text()'
) x
WHERE ad.status_control = 'C'
AND x.commodity_desc IS NOT NULL
AND (xid.submitted_datetime IS NOT NULL OR xid.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""

fa_firearms_authority_certificate_count = """
SELECT count(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = :FA_TYPE
CROSS JOIN XMLTABLE('
for $g1 in /IMA/APP_DETAILS/FA_DETAILS/FIREARMS_AUTHORITIES/AUTHORITY_LIST/AUTHORITY | <null/>
where /IMA/APP_DETAILS/FA_DETAILS/FIREARMS_AUTHORITIES/AUTHORITY_LIST/AUTHORITY and $g1/SELECTED/text()="true"
return
<root>
  <ia_id>{$g1/IA_ID/text()}</ia_id>
  <selected>{$g1/SELECTED/text()}</selected>
</root>
'
PASSING ad.xml_data
COLUMNS
  ia_id INTEGER PATH '/root/ia_id/text()'
  , selected VARCHAR(10) PATH '/root/selected/text()'
) x
WHERE ad.status_control = 'C'
AND (xid.submitted_datetime IS NOT NULL OR xid.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""

sil_section_5_authority_certificate_count = """
SELECT count(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = 'SIL'
CROSS JOIN XMLTABLE('
for $g1 in /IMA/APP_DETAILS/FA_DETAILS/SECTION5_AUTHORITIES/AUTHORITY_LIST/AUTHORITY | <null/>
where /IMA/APP_DETAILS/FA_DETAILS/SECTION5_AUTHORITIES/AUTHORITY_LIST/AUTHORITY and $g1/SELECTED/text()="true"
return
<root>
  <ia_id>{$g1/IA_ID/text()}</ia_id>
  <selected>{$g1/SELECTED/text()}</selected>
</root>
'
PASSING ad.xml_data
COLUMNS
  ia_id INTEGER PATH '/root/ia_id/text()'
  , selected VARCHAR(10) PATH '/root/selected/text()'
) x
WHERE ad.status_control = 'C'
AND (xid.submitted_datetime IS NOT NULL OR xid.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""

# Firearms and Ammunition Bought From Details

fa_bought_from_count = """
SELECT count(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = :FA_TYPE
CROSS JOIN XMLTABLE('
for $g1 in /IMA/APP_DETAILS/SH_DETAILS/SELLER_HOLDER_LIST/SELLER_HOLDER | <null/>
where /IMA/APP_DETAILS/SH_DETAILS/SELLER_HOLDER_LIST/SELLER_HOLDER and not($g1/self::null)
return
<root>
  <sh_id>{$g1/SELLER_HOLDER_ID/text()}</sh_id>
</root>
'
PASSING ad.xml_data
COLUMNS
  sh_id INTEGER PATH '/root/sh_id/text()'
) x
WHERE ad.status_control = 'C'
AND x.sh_id IS NOT NULL
AND (xid.submitted_datetime IS NOT NULL OR xid.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""


# Firearms and Ammunition Supplementary Reports

fa_supplementary_report_count = """
SELECT count(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = :FA_TYPE
CROSS JOIN XMLTABLE('
for $g1 in /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT | <null/>
where /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT and not($g1/self::null)
return
<root>
  <report_id>{$g1/FA_SUPPLEMENTARY_REPORT_DETAILS/FA_REPORT_ID/text()}</report_id>
</root>
'
PASSING ad.xml_data
COLUMNS
  report_id INTEGER PATH '/root/report_id/text()'
) x
WHERE ad.status_control = 'C'
AND x.report_id IS NOT NULL
"""

fa_supplementary_report_upload_count = """
SELECT count(x.file_id)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = :FA_TYPE
CROSS JOIN XMLTABLE('
for $g1 in /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT | <null/>
where /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT and not($g1/self::null)
return
for $g2 in $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE | <null/>
where $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE and not($g2/self::null)
return
for $g3 in $g2/FILE_UPLOAD_LIST/FILE_UPLOAD | <null/>
where $g2/FILE_UPLOAD_LIST/FILE_UPLOAD and not ($g3/self::null)
return
<uploads>
  <file_id>{$g3/FILE_CONTENT/file-id/text()}</file_id>
</uploads>
'
PASSING ad.xml_data
COLUMNS
  file_id VARCHAR(4000) PATH '/uploads/file_id/text()'
) x
WHERE ad.status_control = 'C'
"""

fa_supplementary_report_manual_count = """
SELECT count(x.serial)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = :FA_TYPE
CROSS JOIN XMLTABLE('
for $g1 in /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT | <null/>
where /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT and not($g1/self::null)
return
for $g2 in $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE | <null/>
where $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE and not($g2/self::null)
return
for $g3 in $g2/FIREARMS_DETAILS_LIST/FIREARMS_DETAILS | <null/>
where $g2/FIREARMS_DETAILS_LIST/FIREARMS_DETAILS and not ($g3/self::null)
return
<root>
  <serial>{$g3/SERIAL_NUMBER/text()}</serial>
</root>
'
PASSING ad.xml_data
COLUMNS
  serial VARCHAR(4000) PATH '/root/serial/text()'
) x
WHERE ad.status_control = 'C'
"""

fa_supplementary_report_no_firearm_count = """
SELECT count(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = :FA_TYPE
CROSS JOIN XMLTABLE('
for $g1 in /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT | <null/>
where /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT and not($g1/self::null)
return
for $g2 in $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE | <null/>
where $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE and not($g2/self::null)
return
<root>
  <uploads>{$g2/FILE_UPLOAD_LIST/*}</uploads>
  <details>{$g2/FIREARMS_DETAILS_LIST/*}</details>
  <report_mode>{$g2/FA_REPORTING_MODE/text()}</report_mode>
  <description>{$g2/GOODS_ITEM_DESC/text()}</description>
</root>
'
PASSING ad.xml_data
COLUMNS
  description VARCHAR(4000) PATH '/root/description/text()'
  , report_mode VARCHAR(4000) PATH '/root/report_mode/text()'
  , uploads XMLTYPE PATH '/root/uploads/*'
  , details XMLTYPE PATH '/root/details/*'
) x
WHERE ad.status_control = 'C'
AND x.uploads IS NULL
AND x.details IS NULL
"""

fa_authority_quantity_count = """
SELECT count(*)
FROM impmgr.importer_authorities ia
INNER JOIN impmgr.importer_authority_details iad ON iad.ia_id = ia.id
CROSS JOIN XMLTABLE('
for $g1 in /AUTHORITY/GOODS_CATEGORY_LIST/GOODS_CATEGORY | <null/>
where /AUTHORITY/GOODS_CATEGORY_LIST/GOODS_CATEGORY and $g1/CATEGORY_ID/text()
return
<root>
  <category_id>{$g1/CATEGORY_ID/text()}</category_id>
  <quantity>{$g1/QUANTITY_WRAPPER/QUANTITY/text()}</quantity>
  <unlimited>{$g1/QUANTITY_WRAPPER/UNLIMITED_QUANTITY/text()}</unlimited>
</root>
'
PASSING iad.xml_data
COLUMNS
  category_id INTEGER PATH '/root/category_id/text()'
  , quantity VARCHAR(100) PATH '/root/quantity/text()'
  , unlimited VARCHAR(100) PATH '/root/unlimited/text()'
) x
WHERE iad.status_control = 'C'
AND (quantity > 0 or unlimited = 'true')
AND ia.authority_type = :AUTHORITY_TYPE
"""
