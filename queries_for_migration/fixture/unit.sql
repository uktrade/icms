SELECT
  '[' || LISTAGG(json, ',') WITHIN GROUP( ORDER BY id) || ']'
  FROM (
	SELECT
	  ROW_NUMBER() OVER( ORDER BY UNIT_TYPE) id,
	  '{' || '"pk":' || ROW_NUMBER() OVER( ORDER BY UNIT_TYPE)
		|| ',"model":"web.Unit"'
		|| ',"fields": {'
		|| '"unit_type":"' || unit_type || '"'
		|| ',"description":"' || description || '"'
		|| ',"short_description":"' || short_desc || '"'
		|| ',"hmrc_code":' || hmrc_code
		|| '}'
		|| '}' AS json
	  FROM IMPMGR.UNITS
  )
