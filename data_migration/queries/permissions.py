from django.conf import settings

from data_migration.queries.utils import rp_login

EXCLUDE_DOMAIN = settings.DATA_MIGRATION_EMAIL_DOMAIN_EXCLUDE


user_roles_statement = f"""
FROM (
WITH rp_login AS ({rp_login})
SELECT
  login_id username
  , LISTAGG(DISTINCT xr.res_type || ':' || rmc.role_name, '    ') WITHIN GROUP (ORDER BY xr.res_type, rmc.role_name) roles
FROM appenv.xview_resources xr
INNER JOIN decmgr.resource_members_current rmc ON rmc.res_id = xr.res_id
INNER JOIN decmgr.xview_resource_type_roles xrtr ON xrtr.role_name = rmc.role_name AND xrtr.res_type = xr.res_type
INNER JOIN rp_login ON rp_login.resource_person_id = rmc.person_id
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

importer_user_roles = f"""
WITH rp_login AS (
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
    AND login_id LIKE '%@%'
    AND login_id NOT LIKE '%{EXCLUDE_DOMAIN}' COLLATE BINARY_CI
    AND uah.resource_person_primary_flag = 'Y'
  GROUP BY uah.resource_person_id
)
SELECT
  rp_login.login_id username
  , LISTAGG(DISTINCT xr.res_type || ':' || rmc.role_name, '    ') WITHIN GROUP (ORDER BY xr.res_type, rmc.role_name) roles
  , ur.imp_id importer_id
FROM appenv.xview_resources xr
INNER JOIN decmgr.resource_members_current rmc ON rmc.res_id = xr.res_id
INNER JOIN decmgr.xview_resource_type_roles xrtr ON xrtr.role_name = rmc.role_name AND xrtr.res_type = xr.res_type
INNER JOIN rp_login ON rp_login.resource_person_id = rmc.person_id
LEFT JOIN decmgr.resource_usages_current ru ON ru.res_id = rmc.res_id
LEFT JOIN bpmmgr.urefs ur ON ur.uref = ru.uref
WHERE xr.res_type IN ('IMP_IMPORTER_AGENT_CONTACTS', 'IMP_IMPORTER_CONTACTS')
GROUP BY rp_login.login_id, ur.imp_id
ORDER BY rp_login.login_id
"""

importer_where = """WHERE (
    roles LIKE '%IMP_IMPORTER_AGENT_CONTACTS:EDIT_APP%'
    OR roles LIKE '%IMP_IMPORTER_AGENT_CONTACTS:VARY_APP%'
    OR roles LIKE '%IMP_IMPORTER_AGENT_CONTACTS:VIEW_APP%'
    OR roles LIKE '%IMP_IMPORTER_CONTACTS:AGENT_APPROVER%'
    OR roles LIKE '%IMP_IMPORTER_CONTACTS:EDIT_APP%'
    OR roles LIKE '%IMP_IMPORTER_CONTACTS:VARY_APP%'
    OR roles LIKE '%IMP_IMPORTER_CONTACTS:VIEW_APP%'
)"""

importer_user_roles_count = all_user_roles_count + importer_where


# Exporter Group Permissions

exporter_user_roles = f"""
WITH rp_login AS ({rp_login})
SELECT
  rp_login.login_id username
  , LISTAGG(DISTINCT xr.res_type || ':' || rmc.role_name, '    ') WITHIN GROUP (ORDER BY xr.res_type, rmc.role_name) roles
  , ur.e_id exporter_id
FROM appenv.xview_resources xr
INNER JOIN decmgr.resource_members_current rmc ON rmc.res_id = xr.res_id
INNER JOIN decmgr.xview_resource_type_roles xrtr ON xrtr.role_name = rmc.role_name AND xrtr.res_type = xr.res_type
INNER JOIN rp_login ON rp_login.resource_person_id = rmc.person_id
LEFT JOIN decmgr.resource_usages_current ru ON ru.res_id = rmc.res_id
LEFT JOIN bpmmgr.urefs ur ON ur.uref = ru.uref
WHERE xr.res_type IN ('IMP_EXPORTER_AGENT_CONTACTS', 'IMP_EXPORTER_CONTACTS')
GROUP BY rp_login.login_id, ur.e_id
ORDER BY rp_login.login_id
"""

exporter_where = """WHERE (
    roles LIKE '%IMP_EXPORTER_AGENT_CONTACTS:EDIT_APP%'
    OR roles LIKE '%IMP_EXPORTER_AGENT_CONTACTS:VARY_APP%'
    OR roles LIKE '%IMP_EXPORTER_AGENT_CONTACTS:VIEW_APP%'
    OR roles LIKE '%IMP_EXPORTER_CONTACTS:AGENT_APPROVER%'
    OR roles LIKE '%IMP_EXPORTER_CONTACTS:EDIT_APP%'
    OR roles LIKE '%IMP_EXPORTER_CONTACTS:VARY_APP%'
    OR roles LIKE '%IMP_EXPORTER_CONTACTS:VIEW_APP%'
)"""

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

import_search_where = """WHERE
    roles LIKE '%IMP_ADMIN_SEARCH:SEARCH_CASES%'
    AND roles NOT LIKE '%IMP_CASE_OFFICERS:CASE_OFFICER%'
    AND roles NOT LIKE '%IMP_CASE_OFFICERS:CA_CASE_OFFICER%'
    AND roles NOT LIKE '%IMP_ADMIN:DASHBOARD_USER%'
    AND roles NOT LIKE '%REPORTING_TEAM:REPORT_RUNNER_NOW%'
    AND roles NOT LIKE '%REPORTING_TEAM:REPORT_VIEWER%'
    AND roles NOT LIKE '%IMP_EXTERNAL:SECTION5_AUTHORITY_EDITOR%'
"""

import_search_user_roles = all_user_roles + import_search_where
import_search_user_roles_count = all_user_roles_count + import_search_where

# Constabulary Contacts

constabulary_user_roles = f"""
WITH rp_login AS ({rp_login})
SELECT
  login_id username
  , LISTAGG(DISTINCT xr.res_type || ':' || rmc.role_name, '    ') WITHIN GROUP (ORDER BY xr.res_type, rmc.role_name) roles
  , c.id constabulary_id
FROM appenv.xview_resources xr
INNER JOIN decmgr.resource_members_current rmc ON rmc.res_id = xr.res_id
INNER JOIN decmgr.xview_resource_type_roles xrtr ON xrtr.role_name = rmc.role_name AND xrtr.res_type = xr.res_type
INNER JOIN rp_login ON rp_login.resource_person_id = rmc.person_id
INNER JOIN decmgr.resource_usages_current ru ON ru.res_id = rmc.res_id
INNER JOIN impmgr.constabularies c ON c.uref_value = ru.uref
WHERE xr.res_type IN ('IMP_CONSTABULARY_CONTACTS')
GROUP BY login_id, c.id
ORDER BY login_id, c.id
"""

constabulary_user_roles_count = (
    all_user_roles_count
    + "WHERE roles LIKE '%IMP_CONSTABULARY_CONTACTS:FIREARMS_AUTHORITY_EDITOR%'"
)


users_without_roles_count = f"""
SELECT COUNT(*) FROM (
WITH rp_login AS ({rp_login})
SELECT
  login_id username
  , LISTAGG(DISTINCT xr.res_type || ':' || rmc.role_name, '    ') WITHIN GROUP (ORDER BY xr.res_type, rmc.role_name) roles
FROM rp_login
LEFT JOIN decmgr.resource_members_current rmc ON rp_login.resource_person_id = rmc.person_id
LEFT JOIN appenv.xview_resources xr ON rmc.res_id = xr.res_id
LEFT JOIN decmgr.xview_resource_type_roles xrtr ON xrtr.role_name = rmc.role_name AND xrtr.res_type = xr.res_type
GROUP BY login_id
ORDER BY login_id
) WHERE roles = ':'
"""

roles_summary = f"""
WITH rp_login AS ({rp_login})
SELECT
  xr.res_type || ':' || rmc.role_name roles
  , COUNT(DISTINCT login_id) user_count
FROM appenv.xview_resources xr
INNER JOIN decmgr.resource_members_current rmc ON rmc.res_id = xr.res_id
INNER JOIN decmgr.xview_resource_type_roles xrtr ON xrtr.role_name = rmc.role_name AND xrtr.res_type = xr.res_type
INNER JOIN rp_login ON rp_login.resource_person_id = rmc.person_id
WHERE xr.res_type IN ('IMP_ADMIN', 'IMP_ADMIN_SEARCH', 'IMP_CASE_OFFICERS', 'IMP_EXTERNAL',
  'REPORTING_CATEGORY_MANAGEMENT', 'REPORTING_SUPER_TEAM', 'REPORTING_TEAM', 'IMP_CONSTABULARY_CONTACTS',
  'IMP_EXPORTER_AGENT_CONTACTS', 'IMP_EXPORTER_CONTACTS', 'IMP_IMPORTER_AGENT_CONTACTS', 'IMP_IMPORTER_CONTACTS')
GROUP BY xr.res_type, rmc.role_name
ORDER BY xr.res_type, rmc.role_name
"""
