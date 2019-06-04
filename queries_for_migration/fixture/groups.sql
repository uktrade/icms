SELECT '[' || LISTAGG(team_json, ',') WITHIN GROUP(ORDER BY RES_TYPE_TITLE) || ']' FROM
(
SELECT
     RES_TYPE_TITLE,
	'{'
		||'"pk":' || ROW_NUMBER() over(ORDER BY RES_TYPE_TITLE) || ', '
		|| '"model":"auth.Group",'
		|| '"fields": {'
			|| '"name":"' || res_type_title || '"'
			--|| '"description":"'|| res_type_description || '"'
		|| '}'
	||'}' AS team_json
FROM
	XVIEWMGR.xview_resource_types xrt
WHERE
	SCOPED_WITHIN = 'UNIVERSAL_SET'
ORDER BY RES_TYPE_TITLE
)
