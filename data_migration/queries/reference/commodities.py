commodity_type = """
SELECT
  commodity_type type_code
  , com_type_title type
FROM impmgr.commodity_types ct
"""


commodity_group = """
SELECT
  cg_id id
  , CASE status WHEN 'ACTIVE' THEN 1 ELSE 0 END is_active
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
AND status <> 'ARCHIVED'
"""


commodity = """
SELECT
  com_id id
  , CASE status WHEN 'ACTIVE' THEN 1 ELSE 0 END is_active
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
SELECT cg_id commoditygroup_id, com_id commodity_id
FROM impmgr.xview_com_group_commodities cgc
WHERE status_control = 'C'
AND status <> 'ARCHIVED'
"""


unit = """
SELECT unit_type, description, short_desc short_description, hmrc_code
FROM impmgr.units
"""


commodity_timestamp_update = """
UPDATE web_commodity SET start_datetime = data_migration_commodity.start_datetime
FROM data_migration_commodity
WHERE web_commodity.id = data_migration_commodity.id
"""


commodity_group_timestamp_update = """
UPDATE web_commoditygroup SET start_datetime = data_migration_commoditygroup.start_datetime
FROM data_migration_commoditygroup
WHERE web_commoditygroup.id = data_migration_commoditygroup.id
"""
