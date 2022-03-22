constabularies = """
SELECT
  con_id id
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , constabulary_name name
  , constabulary_region region
  , email_address email
FROM IMPMGR.XVIEW_CONSTABULARY_DETAILS xcd
WHERE STATUS_CONTROL = 'C'
ORDER BY con_id
"""
