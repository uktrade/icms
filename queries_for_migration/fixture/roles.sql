WITH team_role_privs as (

    SELECT
    max(team_id) over() + role_id AS role_group_id
    ,t.*
    FROM (
		SELECT
		  dense_rank() over(ORDER BY rt.res_type_title) AS team_id
		  ,dense_rank() over(ORDER BY rt.res_type,rtr.role_name) AS role_id
		  ,dense_rank() over(ORDER BY rt.res_type, rtp.DEFAULT_SYSTEM_PRIV) + 100 AS priv_id
		  ,rt.RES_TYPE_TITLE AS team_name
		  ,REPLACE(REPLACE(rt.res_type_description, '"','\"'), chr(10), '\n')  AS team_description
		  ,rt.res_type_title||':'||rtr.role_title AS role_name
		  ,REPLACE(REPLACE(rtr.role_description, '"','\"'), chr(10), '\n')  AS role_description
		  ,substr(
			  CASE
				  WHEN rtp.DEFAULT_SYSTEM_PRIV IS NULL THEN rtr.ROLE_NAME || '_' || rt.RES_TYPE
				  ELSE rtp.DEFAULT_SYSTEM_PRIV || '_' || rtr.ROLE_NAME || '_' || rt.RES_TYPE END
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
	) t

)



-- Roles
SELECT
	'[' || LISTAGG(json, ',') WITHIN GROUP( ORDER BY id) || ']' FROM (
	SELECT
		 id,
		'{' || '"pk":' || id
			|| ',"model":"auth.Group"'
			|| ',"fields": {'
				|| '"name":"' || name || '"'
				|| ',"permissions":' || permissions
			 || '}'
		 || '},'
		 || '{' || '"pk":' || id
				|| ',"model":"web.Role"'
				|| ',"fields": {'
					|| '"group_id":"' || id || '"'
					|| ',"description":"' || DESCRIPTION || '"'
				|| '}'
		|| '}'

		 AS json
	FROM (
		SELECT
			role_id AS id,
			role_name AS name,
			role_description AS description,
			'[' || LISTAGG(priv_id,',') WITHIN GROUP (ORDER BY priv_id)  || ']' AS permissions
		FROM team_role_privs
		GROUP BY  role_id, role_name, role_description
	)
)
