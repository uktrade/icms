-- Country groups data
SELECT
  groups.country_group_detail_id AS pk,
  groups.group_name AS name,
  groups.group_comments  AS comments,
  countries.countries
  FROM XVIEWMGR.XVIEW_COUNTRY_GROUPS groups
       , (
         SELECT
	       country_group_detail_id AS group_id,
	       LISTAGG(country_id, ',') WITHIN GROUP(ORDER BY country_id) AS countries
           FROM XVIEWMGR.XVIEW_COUNTRY_GROUP_COUNTRIES
          WHERE country_id IN (SELECT country_id FROM XVIEWMGR.XV_COUNTRY_DETAILS_DATA)
          GROUP BY country_group_detail_id
       ) countries
 WHERE groups.country_group_detail_id=countries.group_id(+)
