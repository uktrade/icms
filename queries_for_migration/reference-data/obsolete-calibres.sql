-- Obsolete calibre items data
SELECT
  id AS pk
  , PARENT_OC_ID AS calibre_group_id
  , CASE WHEN status='CURRENT' THEN 'True' ELSE 'False' END AS is_active
  , calibre_name AS name
  , ordinal AS "ORDER"
  FROM IMPMGR.OBSOLETE_CALIBRES oc
 WHERE oc.PARENT_OC_ID IS NOT NULL
