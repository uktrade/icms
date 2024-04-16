export_application_template = """
SELECT
  id
  , name
  , description
  , ca_type application_type
  , CASE share_level WHEN 'NONE' THEN 'PRIVATE' ELSE share_level END sharing
  , owner_wua_id owner_id
  , created_datetime
  , CASE WHEN last_updated_datetime IS NULL THEN created_datetime ELSE last_updated_datetime END last_updated_datetime
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , xml_data cat_xml
FROM impmgr.certificate_app_templates cat
ORDER BY id
"""


cfs_application_template = """
SELECT rownum id, t.*
FROM (
  SELECT
    id template_id
    , x.countries_xml
    , x.schedules_xml
  FROM impmgr.certificate_app_templates cat
  CROSS JOIN XMLTABLE(
    '/*'
    PASSING cat.xml_data
    COLUMNS
      countries_xml XMLTYPE PATH '/CA/APPLICATION/COUNTRIES'
      , schedules_xml XMLTYPE PATH '/CA/APPLICATION/PRODUCTS/*'
  ) x
  WHERE ca_type = 'CFS'
  ORDER BY template_id
) t
"""


com_application_template = """
SELECT rownum id, t.*
FROM (
  SELECT
    id template_id
    , CASE x.is_free_sale_uk WHEN 'true' THEN 1 WHEN 'false' THEN 0 ELSE NULL END is_free_sale_uk
    , CASE x.is_manufacturer WHEN 'true' THEN 1 WHEN 'false' THEN 0 ELSE NULL END is_manufacturer
    , x.product_name
    , x.chemical_name
    , x.manufacturing_process
    , x.countries_xml
  FROM impmgr.certificate_app_templates cat
  CROSS JOIN XMLTABLE(
    '*'
    PASSING cat.xml_data
    COLUMNS
      countries_xml XMLTYPE PATH '/CA/APPLICATION/COUNTRIES'
      , is_free_sale_uk VARCHAR2(20) PATH '/CA/APPLICATION//PRODUCTS/SCHEDULE_LIST/SCHEDULE/IS_DOMESTIC_MARKET_PESTICIDE/text()'
      , is_manufacturer VARCHAR2(20) PATH '/CA/APPLICATION//PRODUCTS/SCHEDULE_LIST/SCHEDULE/IS_DOMESTIC_MARKET_PESTICIDE/IS_PESTICIDE_MANUFACTURER/text()'
      , product_name VARCHAR2(20) PATH '/CA/APPLICATION//PRODUCTS/SCHEDULE_LIST/SCHEDULE/IS_DOMESTIC_MARKET_PESTICIDE/PRODUCT_LIST/PRODUCT/NAME/text()'
      , chemical_name VARCHAR2(20) PATH
        '/CA/APPLICATION//PRODUCTS/SCHEDULE_LIST/SCHEDULE/IS_DOMESTIC_MARKET_PESTICIDE/PRODUCT_LIST/PRODUCT/CHEMICAL_NAME/text()'
      , manufacturing_process VARCHAR2(20) PATH
        '/CA/APPLICATION//PRODUCTS/SCHEDULE_LIST/SCHEDULE/IS_DOMESTIC_MARKET_PESTICIDE/PRODUCT_LIST/PRODUCT/MANUFACTURING_PROCESS/text()'
  ) x
  WHERE ca_type = 'COM'
  ORDER BY template_id
) t
"""


cat_timestamp_update = """
UPDATE web_certificateapplicationtemplate
SET created_datetime = dm_cat.created_datetime
, last_updated_datetime = dm_cat.last_updated_datetime
FROM data_migration_certificateapplicationtemplate dm_cat
WHERE web_certificateapplicationtemplate.id = dm_cat.id
"""


cfs_template_timestamp_update = """
UPDATE web_certificateoffreesaleapplicationtemplate
SET last_update_datetime = dm_cat.last_updated_datetime
FROM data_migration_certificateapplicationtemplate dm_cat
WHERE web_certificateoffreesaleapplicationtemplate.template_id = dm_cat.id
"""


com_template_timestamp_update = """
UPDATE web_certificateofmanufactureapplicationtemplate
SET last_update_datetime = dm_cat.last_updated_datetime
FROM data_migration_certificateapplicationtemplate dm_cat
WHERE web_certificateofmanufactureapplicationtemplate.template_id = dm_cat.id
"""


cfs_schedule_template_timestamp_update = """
UPDATE web_cfsscheduletemplate
SET created_at = dm_cat.last_updated_datetime
, updated_at = dm_cat.last_updated_datetime
FROM data_migration_cfsscheduletemplate dm_st
INNER JOIN data_migration_certificateoffreesaleapplicationtemplate dm_cfst ON dm_cfst.id = dm_st.application_id
INNER JOIN data_migration_certificateapplicationtemplate dm_cat ON dm_cat.id = dm_cfst.template_id
WHERE web_cfsscheduletemplate.id = dm_st.id
"""
