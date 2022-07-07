__all__ = ["importers", "offices"]

# After users migrated
# , wua_id user_id

importers = """
SELECT
  imp_id id
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , imp_entity_type type
  , organisation_name name
  , reg_number registered_number
  , eori_number
  , 2 user_id
  , main_imp_id main_importer_id
  , other_coo_code region_origin
FROM impmgr.xview_importer_details xid
WHERE status_control = 'C'
ORDER BY imp_id
"""


offices = """
SELECT
  rownum id
  , imp_id importer_id
  , imp_id || '-' || office_id legacy_id
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , postcode
  , address
  , eori_number
  , address_entry_type
FROM impmgr.xview_importer_offices xio
WHERE status_control = 'C'
ORDER BY imp_id, office_id
"""
