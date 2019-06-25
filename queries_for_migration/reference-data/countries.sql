--- Countries data

SELECT
  c.country_id AS pk,
  c.country_name AS name,
  c.country_type AS type,
  CASE WHEN c.country_status='ACTIVE' THEN 'True' ELSE 'False' END AS is_active,
  attrs.commission_code,
  attrs.hmrc_code
  FROM
	  XVIEWMGR.XV_COUNTRY_DETAILS_DATA c,
	( SELECT
	    country_id,
	    min(CASE WHEN name='COMMISSION_CODE' THEN value END) AS commission_code,
	    min(CASE WHEN name='HMRC_CODE' THEN value END) AS hmrc_code
	    FROM XVIEWMGR.XV_CNTRY_ATTR_ALL_DATA a
	   GROUP BY country_id
	) attrs
 WHERE
	c.COUNTRY_ID=attrs.COUNTRY_ID(+)
