__all__ = ["commodity_type", "commodity_group", "commodity", "commodity_group_commodity", "unit"]


commodity_type = (
    "SELECT commodity_type type_code, com_type_title type FROM impmgr.commodity_types ct"
)


commodity_group = """
SELECT cg_id id
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
SELECT DISTINCT cg_id commoditygroup_id, com_id commodity_id
FROM impmgr.xview_com_group_commodities
"""


unit = """
SELECT unit_type, description, short_desc short_description, hmrc_code
FROM impmgr.units
"""
