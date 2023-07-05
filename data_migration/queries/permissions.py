user_roles_statement = """
FROM (
WITH rp_wua AS (
  SELECT uah.resource_person_id
  , CASE
    WHEN COUNT(login_id) > 1
    THEN (
      SELECT sub.login_id
      FROM securemgr.web_user_account_histories sub
      WHERE sub.person_id_current IS NOT NULL
        AND sub.resource_person_primary_flag = 'Y'
        AND sub.resource_person_id = uah.resource_person_id
        AND sub.account_status = 'ACTIVE'
    )
    ELSE MAX(login_id)
  END login_id
  FROM securemgr.web_user_account_histories uah
  WHERE uah.person_id_current IS NOT NULL
    AND uah.resource_person_primary_flag = 'Y'
  GROUP BY uah.resource_person_id
)
SELECT
  login_id username
  , LISTAGG(DISTINCT xr.res_type || ':' || rmc.role_name, '    ') WITHIN GROUP (ORDER BY xr.res_type, rmc.role_name) roles
FROM appenv.xview_resources xr
INNER JOIN decmgr.resource_members_current rmc ON rmc.res_id = xr.res_id
INNER JOIN decmgr.xview_resource_type_roles xrtr ON xrtr.role_name = rmc.role_name AND xrtr.res_type = xr.res_type
INNER JOIN rp_wua ON rp_wua.resource_person_id = rmc.person_id
WHERE xr.res_type IN ('IMP_ADMIN', 'IMP_ADMIN_SEARCH', 'IMP_CASE_OFFICERS', 'IMP_EXTERNAL',
  'REPORTING_CATEGORY_MANAGEMENT', 'REPORTING_SUPER_TEAM', 'REPORTING_TEAM', 'IMP_CONSTABULARY_CONTACTS',
  'IMP_EXPORTER_AGENT_CONTACTS', 'IMP_EXPORTER_CONTACTS', 'IMP_IMPORTER_AGENT_CONTACTS', 'IMP_IMPORTER_CONTACTS')
GROUP BY login_id
ORDER BY login_id
)
"""

all_user_roles = "SELECT *" + user_roles_statement
all_user_roles_count = "SELECT COUNT(*)" + user_roles_statement


# Importer Group Permissions

importer_where = """WHERE (
    roles LIKE '%IMP_IMPORTER_AGENT_CONTACTS:EDIT_APP%'
    OR roles LIKE '%IMP_IMPORTER_AGENT_CONTACTS:VARY_APP%'
    OR roles LIKE '%IMP_IMPORTER_AGENT_CONTACTS:VIEW_APP%'
    OR roles LIKE '%IMP_IMPORTER_CONTACTS:AGENT_APPROVER%'
    OR roles LIKE '%IMP_IMPORTER_CONTACTS:EDIT_APP%'
    OR roles LIKE '%IMP_IMPORTER_CONTACTS:VARY_APP%'
    OR roles LIKE '%IMP_IMPORTER_CONTACTS:VIEW_APP%'
)"""

importer_user_roles = all_user_roles + importer_where
importer_user_roles_count = all_user_roles_count + importer_where


# Exporter Group Permissions

exporter_where = """WHERE (
    roles LIKE '%IMP_EXPORTER_AGENT_CONTACTS:EDIT_APP%'
    OR roles LIKE '%IMP_EXPORTER_AGENT_CONTACTS:VARY_APP%'
    OR roles LIKE '%IMP_EXPORTER_AGENT_CONTACTS:VIEW_APP%'
    OR roles LIKE '%IMP_EXPORTER_CONTACTS:AGENT_APPROVER%'
    OR roles LIKE '%IMP_EXPORTER_CONTACTS:EDIT_APP%'
    OR roles LIKE '%IMP_EXPORTER_CONTACTS:VARY_APP%'
    OR roles LIKE '%IMP_EXPORTER_CONTACTS:VIEW_APP%'
)"""

exporter_user_roles = all_user_roles + exporter_where
exporter_user_roles_count = all_user_roles_count + exporter_where


# ILB Case Officer Group Permissions

ilb_where = "WHERE roles LIKE '%IMP_CASE_OFFICERS:CASE_OFFICER%' AND roles LIKE '%IMP_CASE_OFFICERS:CA_CASE_OFFICER%'"
ilb_user_roles = all_user_roles + ilb_where
ilb_user_roles_count = all_user_roles_count + ilb_where


# Home Office Case Officer Group Permissions

home_office_where = """WHERE
    NOT (roles LIKE '%IMP_CASE_OFFICERS:CASE_OFFICER%' AND roles LIKE '%IMP_CASE_OFFICERS:CA_CASE_OFFICER%')
    AND roles LIKE '%IMP_EXTERNAL:SECTION5_AUTHORITY_EDITOR%'
    AND roles LIKE '%IMP_ADMIN_SEARCH:SEARCH_CASES%'
"""

home_office_user_roles = all_user_roles + home_office_where
home_office_user_roles_count = all_user_roles_count + home_office_where


# NCA Case Officer Group Permissions

nca_where = """WHERE
    NOT (roles LIKE '%IMP_CASE_OFFICERS:CASE_OFFICER%' AND roles LIKE '%IMP_CASE_OFFICERS:CA_CASE_OFFICER%')
    AND roles LIKE '%IMP_ADMIN:DASHBOARD_USER%'
    AND roles LIKE '%REPORTING_TEAM:REPORT_RUNNER_NOW%'
    AND roles LIKE '%REPORTING_TEAM:REPORT_VIEWER%'
"""

nca_user_roles = all_user_roles + nca_where
nca_user_roles_count = all_user_roles_count + nca_where


users_without_roles_count = """
SELECT count(*) FROM (
WITH rp_wua AS (
  SELECT uah.resource_person_id
  , CASE
    WHEN COUNT(login_id) > 1
    THEN (
      SELECT sub.login_id
      FROM securemgr.web_user_account_histories sub
      WHERE sub.person_id_current IS NOT NULL
        AND sub.resource_person_primary_flag = 'Y'
        AND sub.resource_person_id = uah.resource_person_id
        AND sub.account_status = 'ACTIVE'
    )
    ELSE MAX(login_id)
  END login_id
  FROM securemgr.web_user_account_histories uah
  WHERE uah.person_id_current IS NOT NULL
    AND uah.resource_person_primary_flag = 'Y'
  GROUP BY uah.resource_person_id
)
SELECT
  login_id username
FROM rp_wua
LEFT JOIN decmgr.resource_members_current rmc ON rmc.person_id = rp_wua.resource_person_id
LEFT JOIN appenv.xview_resources xr ON xr.res_id = rmc.res_id
WHERE rmc.rd_id IS null
GROUP BY login_id
ORDER BY login_id
)
"""

roles_summary = """
WITH rp_wua AS (
  SELECT uah.resource_person_id
  , CASE
    WHEN COUNT(login_id) > 1
    THEN (
      SELECT sub.login_id
      FROM securemgr.web_user_account_histories sub
      WHERE sub.person_id_current IS NOT NULL
        AND sub.resource_person_primary_flag = 'Y'
        AND sub.resource_person_id = uah.resource_person_id
        AND sub.account_status = 'ACTIVE'
    )
    ELSE MAX(login_id)
  END login_id
  FROM securemgr.web_user_account_histories uah
  WHERE uah.person_id_current IS NOT NULL
    AND uah.resource_person_primary_flag = 'Y'
  GROUP BY uah.resource_person_id
)
SELECT
  xr.res_type || ':' || rmc.role_name roles
  , COUNT(DISTINCT login_id) user_count
FROM appenv.xview_resources xr
INNER JOIN decmgr.resource_members_current rmc ON rmc.res_id = xr.res_id
INNER JOIN decmgr.xview_resource_type_roles xrtr ON xrtr.role_name = rmc.role_name AND xrtr.res_type = xr.res_type
INNER JOIN rp_wua ON rp_wua.resource_person_id = rmc.person_id
WHERE xr.res_type IN ('IMP_ADMIN', 'IMP_ADMIN_SEARCH', 'IMP_CASE_OFFICERS', 'IMP_EXTERNAL',
  'REPORTING_CATEGORY_MANAGEMENT', 'REPORTING_SUPER_TEAM', 'REPORTING_TEAM', 'IMP_CONSTABULARY_CONTACTS',
  'IMP_EXPORTER_AGENT_CONTACTS', 'IMP_EXPORTER_CONTACTS', 'IMP_IMPORTER_AGENT_CONTACTS', 'IMP_IMPORTER_CONTACTS')
GROUP BY xr.res_type, rmc.role_name
ORDER BY xr.res_type, rmc.role_name
"""
