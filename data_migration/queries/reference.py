country = """
  SELECT country_id id, x.*
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
  WHERE end_datetime IS NULL OR country_id = 155
"""


country_group = """
  SELECT country_group_detail_id id, country_group_id, group_name name, group_comments comments
  FROM bpmmgr.xview_country_groups xcg
  WHERE group_status = 'ACTIVE'
"""


country_group_country = """
  SELECT xcgc.country_group_detail_id countrygroup_id, xcgc.country_id
  FROM bpmmgr.xview_country_group_countries xcgc
  INNER JOIN bpmmgr.xview_country_groups xcg ON xcg.country_group_detail_id = xcgc.country_group_detail_id
  WHERE xcg.group_status = 'ACTIVE'
"""


country_translation_set = "SELECT id, name, status FROM bpmmgr.country_translation_sets cts"


country_translation = """
  SELECT id, translated_country_name translation, country_id, country_translation_set_id translation_set_id
  FROM bpmmgr.country_translations
"""


commodity_type = (
    "SELECT rownum id, commodity_type type_code, com_type_title type FROM impmgr.commodity_types ct"
)


commodity_group = """
  SELECT cg_id id
    , status
    , group_type
    , group_code
    , group_name
    , group_description
    , start_datetime
    , end_datetime
    , commodity_type commodity_type_id
    , unit unit_id
  FROM impmgr.xview_com_group_details xcgd
  WHERE status_control = 'C'
"""


commodity = """
  SELECT
    com_id id
    , status
    , commodity_code
    , commodity_type commodity_type_id
    , validity_start_date
    , validity_end_date
    , quantity_threshold
    , sigl_product_type
    , start_datetime
    , end_datetime
  FROM impmgr.commodity_details cd
  WHERE status_control = 'C'
"""


commodity_group_commodity = """
  SELECT DISTINCT cg_id commoditygroup_id, com_id commodity_id
  FROM impmgr.xview_com_group_commodities
"""


unit = """
SELECT unit_type, description, short_desc short_description, hmrc_code
FROM impmgr.units
"""
