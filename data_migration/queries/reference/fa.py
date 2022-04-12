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
