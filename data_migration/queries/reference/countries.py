country = """
  SELECT
    country_id id
    , x.name
    , CASE x.status WHEN 'ACTIVE' THEN 1 ELSE 0 END is_active
    , x.type
    , x.commission_code
    , x.hmrc_code
  FROM bpmmgr.country_details cd,
    XMLTABLE('/*'
      PASSING cd.xml_data
      COLUMNS
        name VARCHAR2(100) PATH '/COUNTRY/COUNTRY_NAME/text()'
        , status VARCHAR2(10) PATH '/COUNTRY/COUNTRY_STATUS[text()="ACTIVE"]/text()'
        , type VARCHAR2 (30) PATH '/COUNTRY/COUNTRY_TYPE/text()'
        , commission_code VARCHAR(6) PATH '/COUNTRY/ATTRIBUTE_LIST/ATTRIBUTE_SET/ATTRIBUTE[NAME="COMMISSION_CODE"]/VALUE/text()'
        , hmrc_code VARCHAR2(4) PATH '/COUNTRY/ATTRIBUTE_LIST/ATTRIBUTE_SET/ATTRIBUTE[NAME="HMRC_CODE"]/VALUE/text()'
    ) x
  WHERE end_datetime IS NULL
"""


country_group = """
SELECT
  country_group_detail_id id
  , country_group_id
  , group_name name
  , group_comments comments
FROM bpmmgr.xview_country_groups xcg
WHERE group_status = 'ACTIVE'
"""


country_group_country = """
SELECT
  cg.id countrygroup_id
  , cgc.country_id
FROM bpmmgr.country_group_countries cgc
INNER JOIN bpmmgr.country_group_details cg ON cg.country_group_id = cgc.country_group_id
WHERE cg.end_datetime IS NULL
"""


country_translation_set = """
SELECT
  id
  , name
  , CASE status WHEN 'ACTIVE' THEN 1 ELSE 0 END is_active
FROM bpmmgr.country_translation_sets cts
"""


country_translation = """
SELECT
  id
  , translated_country_name translation
  , country_id
  , country_translation_set_id translation_set_id
FROM bpmmgr.country_translations
"""
