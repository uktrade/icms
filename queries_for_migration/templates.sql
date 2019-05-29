SELECT
	td.t_id AS pk,
	TO_CHAR(td.START_DATETIME, 'DD-MON-YYYY HH24:MI:SS') start_datetime,
	TO_CHAR(td.END_DATETIME, 'DD-MON-YYYY HH24:MI:SS') end_datetime,
	CASE
		WHEN td.TEMPLATE_STATUS = 'ACTIVE' THEN 'True'
		ELSE 'False'
	END AS is_active,
	td.TEMPLATE_NAME,
	td.TEMPLATE_MNEM AS template_code,
	td.TEMPLATE_TYPE,
	td.APPLICATION_DOMAIN,
	CASE
		WHEN td.TEMPLATE_TYPE = 'EMAIL_TEMPLATE' THEN xtd.email_subject
		WHEN td.TEMPLATE_TYPE = 'DECLARATION' THEN xtd.declaration_title
		ELSE NULL
	END AS template_title,
	CASE
		WHEN td.TEMPLATE_TYPE = 'EMAIL_TEMPLATE' THEN xtd.email_body
		WHEN td.TEMPLATE_TYPE = 'DECLARATION' THEN xtd.declaration_text
		WHEN td.TEMPLATE_TYPE = 'ENDORSEMENT' THEN xtd.endorsement_text
		WHEN td.TEMPLATE_TYPE = 'LETTER_TEMPLATE' THEN TO_CHAR(SUBSTR(xtd.letter_body,1,4000))
    	WHEN td.TEMPLATE_TYPE = 'CFS_TRANSLATION' THEN TO_CHAR(SUBSTR(xtd.translation_body,1,4000))
		ELSE NULL
	END AS template_content
FROM
	XVIEWMGR.XVIEW_TEMPLATE_DETAILS xtd,
	IMPMGR.TEMPLATE_DETAILS td
WHERE
	td.t_id = xtd.t_id
	AND xtd.status_control = 'C'
	AND td.STATUS_CONTROL = 'C'
ORDER BY
	td.t_id ASC
