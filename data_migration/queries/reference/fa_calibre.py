constabularies = """
SELECT
  con_id id
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , constabulary_name name
  , constabulary_region region
  , email_address email
FROM impmgr.xview_constabulary_details xcd
WHERE status_control = 'C'
ORDER BY con_id
"""


obsolete_calibre_group = """
SELECT
  ROWNUM id
  , ocs.*
FROM (
  SELECT
    id legacy_id
    , calibre_name name
    , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
    , ordinal "order"
  FROM impmgr.obsolete_calibres oc
  WHERE parent_oc_id IS NULL
  ORDER BY legacy_id
) ocs
"""


obsolete_calibre = """
SELECT
  ROWNUM id
  , ocs.*
FROM (
  SELECT
    id legacy_id
    , calibre_name name
    , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
    , ordinal "order"
    , parent_oc_id calibre_group_id
  FROM impmgr.obsolete_calibres oc
  WHERE parent_oc_id IS NOT NULL
  ORDER BY legacy_id
) ocs
"""
