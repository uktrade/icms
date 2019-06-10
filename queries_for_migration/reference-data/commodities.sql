SELECT
  cd.com_id AS pk
  , CASE WHEN cd.status = 'ARCHIVED' THEN 'False' ELSE 'True' END AS is_active
  ,TO_CHAR(cd.START_DATETIME, 'DD-MON-YYYY HH24:MI:SS') start_datetime
  ,TO_CHAR(cd.END_DATETIME, 'DD-MON-YYYY HH24:MI:SS') end_datetime
  , cd.commodity_code
  , cd.commodity_type
  ,TO_CHAR(cd.VALIDITY_START_DATE, 'DD-MON-YYYY') VALIDITY_START_DATE
  ,TO_CHAR(cd.VALIDITY_END_DATE, 'DD-MON-YYYY') VALIDITY_END_DATE
  , cd.QUANTITY_THRESHOLD
  , cd.SIGL_PRODUCT_TYPE
  FROM impmgr.commodity_details cd
 WHERE cd.status_control = 'C'
 ORDER BY commodity_code
