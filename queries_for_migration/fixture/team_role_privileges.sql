WITH team_role_privs as (

    SELECT
    max(team_id) over() + role_id AS role_group_id
    ,t.*
    FROM (
		SELECT
		  dense_rank() over(ORDER BY rt.res_type_title) AS team_id
		  ,dense_rank() over(ORDER BY rt.res_type,rtr.role_name) AS role_id
		  ,dense_rank() over(ORDER BY rt.res_type, rtp.DEFAULT_SYSTEM_PRIV) + 1000 AS priv_id
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

-- Permissions
SELECT '[' || LISTAGG(json, ',') WITHIN GROUP( ORDER BY id) || ']' FROM (
	SELECT
			 id,
			'{' || '"pk":' || id
				|| ',"model":"auth.Permission"'
				|| ',"fields": {'
					|| '"name":"' || name || '"'
					|| ',"content_type_id":' || 12 || ''
					|| ',"codename":"'|| name || '"'
				 || '}'
			 || '}' AS json

	from (
		SELECT  DISTINCT PRIV_ID AS id, PRIVILEGE AS name FROM team_role_privs
	)
)


-- Groups ( with permissions linked)

SELECT
	'[' || LISTAGG(json, ',') WITHIN GROUP( ORDER BY id) || ']'
FROM
(
	SELECT
		 id,
		'{' || '"pk":' || id
			|| ',"model":"auth.Group"'
			|| ',"fields": {'
				|| '"name":"' || name || '"'
				|| ',"permissions":' || privs || ''
			 || '}'
		 || '}' AS json
	FROM (
		SELECT DISTINCT team_id AS id, TEAM_NAME AS name, '[]' AS privs FROM team_role_privs
		UNION ALL
		SELECT role_group_id, ROLE_NAME, '[' || LISTAGG(priv_id, ',') WITHIN GROUP(ORDER BY role_group_id) || ']' FROM team_role_privs GROUP BY role_group_id, role_name
	)
)



-- Teams
SELECT
	'[' || LISTAGG(json, ',') WITHIN GROUP( ORDER BY id) || ']' FROM (
SELECT
	 id,
	'{' || '"pk":' || id
		|| ',"model":"web.Team"'
		|| ',"fields": {'
			|| '"group_id":"' || id || '"'
			|| ',"name":"' || name || '"'
			|| ',"description":"' || DESCRIPTION || '"'
		 || '}'
	 || '}' AS json
FROM (
	SELECT DISTINCT team_id AS id, team_name AS name, team_description AS description FROM team_role_privs
))



-- Roles
SELECT
	'[' || LISTAGG(json, ',') WITHIN GROUP( ORDER BY id) || ']' FROM (
SELECT
	 id,
	'{' || '"pk":' || id
		|| ',"model":"web.Role"'
		|| ',"fields": {'
			|| '"group_id":"' || group_id || '"'
			|| ',"team_id":"' || team_id || '"'
			|| ',"name":"' || name || '"'
			|| ',"description":"' || DESCRIPTION || '"'
		 || '}'
	 || '}' AS json
FROM (
	SELECT DISTINCT role_group_id AS group_id, team_id, role_id AS id, role_name AS name, role_description AS description FROM team_role_privs
))
