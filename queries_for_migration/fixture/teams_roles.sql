WITH team_role_privs as (

	SELECT
	  dense_rank() over(ORDER BY rt.res_type_title) AS team_id
	  ,dense_rank() over(ORDER BY rt.res_type,rtr.role_name) AS role_id
	  ,dense_rank() over(ORDER BY rt.res_type, rtp.DEFAULT_SYSTEM_PRIV) + 1000 AS priv_id
	  ,rt.RES_TYPE_TITLE AS team_name
	  ,REPLACE(REPLACE(rt.res_type_description, '"','\"'), chr(10), '\n')  AS team_description
	  ,rt.res_type_title||':'||rtr.role_title AS role_name
	  ,REPLACE(REPLACE(rtr.role_description, '"','\"'), chr(10), '\n')  AS role_description
	  ,rtr.display_seq AS role_order
	  ,substr(
		  CASE
			  WHEN rtp.DEFAULT_SYSTEM_PRIV IS NULL THEN rtr.ROLE_NAME || ':' || rt.RES_TYPE
			  ELSE rtp.DEFAULT_SYSTEM_PRIV || ':' || rtr.ROLE_NAME || ':' || rt.RES_TYPE END
		,0, 100) AS privilege
	  FROM
		  XVIEWMGR.XVIEW_RESOURCE_TYPES rt
		,XVIEWMGR.XVIEW_RESOURCE_TYPE_ROLES rtr
		,XVIEWMGR.XVIEW_RESOURCE_TYPE_PRIVS rtp
	 WHERE
		rt.res_type = rtr.res_type
	AND rt.SCOPED_WITHIN='UNIVERSAL_SET'
	AND rtr.RES_TYPE=rtp.RES_TYPE(+)
	AND rtr.ROLE_NAME=rtp.ROLE_NAME(+)

)


SELECT '[' || LISTAGG(json,',') WITHIN GROUP (ORDER BY rownum)  || ']'
FROM (
  SELECT
      role_id,
      '{' || '"pk":' || role_id
          || ',"model":"auth.Group"'
          || ',"fields": {'
              || '"name":"' || role_name || '"'
              || ',"permissions":' || '[' || LISTAGG(priv_id,',') WITHIN GROUP (ORDER BY priv_id)  || ']'
          || '}'
      || '},'
      || '{' || '"pk":' || role_id
              || ',"model":"web.Role"'
              || ',"fields": {'
                  || '"group_id":"' || role_id || '"'
                  || ',"description":"' || role_description || '"'
                  || ',"role_order":"' || role_order || '"'
              || '}'
      || '}'
      AS json
  FROM team_role_privs
  GROUP BY  role_id, role_name, role_description, role_order

  UNION ALL 

  SELECT
      team_id,
      '{' || '"pk":' || team_id
          || ',"model":"web.Team"'
          || ',"fields": {'
              || '"name":"' || team_name || '"'
              || ',"description":"' || team_description || '"'
              || ',"roles":' || '[' || LISTAGG(role_id, ',' ) WITHIN GROUP(ORDER BY role_id) || ']'
          || '}'
      || '}' AS json
      FROM team_role_privs GROUP BY team_id, team_name, team_description
)


