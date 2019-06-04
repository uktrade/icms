SELECT
  cd.CON_ID AS pk ,
  cd.constabulary_name AS name ,
  cd.constabulary_region AS region,
  cd.email_address as email,
  CASE
  WHEN cd.status = 'CURRENT' THEN 'True'
  ELSE 'False'
  END is_active
  FROM
	  impmgr.xview_constabulary_details cd
 WHERE
	cd.status_control = 'C'
 ORDER BY
	cd.constabulary_name
