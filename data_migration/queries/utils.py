from django.conf import settings

EXCLUDE_DOMAIN = settings.DATA_MIGRATION_EMAIL_DOMAIN_EXCLUDE

# Used as a with statement to connect wua_id to resource_person_id.
# Instances where there are two web user accounts are associated with a resource person account, take the active web user account
# In the instances with two web user accounts, the log in id is the same on both accounts but one has account status cancelled
rp_wua = """
  SELECT
  uah.resource_person_id
  , CASE
    WHEN COUNT(wua_id) > 1
    THEN (
      SELECT sub.wua_id
      FROM securemgr.web_user_account_histories sub
      WHERE sub.person_id_current IS NOT NULL
        AND sub.resource_person_primary_flag = 'Y'
        AND sub.resource_person_id = uah.resource_person_id
        AND sub.account_status = 'ACTIVE'
    )
    ELSE MAX(wua_id)
  END wua_id
  FROM securemgr.web_user_account_histories uah
  WHERE uah.person_id_current IS NOT NULL
    AND uah.resource_person_primary_flag = 'Y'
  GROUP BY uah.resource_person_id
"""

# Used as a with statement to create a temporary table that connects resource_person_id with login_id
# When multiple login_ids, take the login_id of the active account
# Exclude login ids with the excluded domain in the email address

rp_login = f"""
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
  , CASE
    WHEN COUNT(login_id) > 1
    THEN (
      SELECT sub.account_status
      FROM securemgr.web_user_account_histories sub
      WHERE sub.person_id_current IS NOT NULL
        AND sub.resource_person_primary_flag = 'Y'
        AND sub.resource_person_id = uah.resource_person_id
        AND sub.account_status = 'ACTIVE'
    )
    ELSE MAX(account_status)
  END account_status
  FROM securemgr.web_user_account_histories uah
  WHERE uah.person_id_current IS NOT NULL
    AND login_id LIKE '%@%'
    AND login_id NOT LIKE '%{EXCLUDE_DOMAIN}' COLLATE BINARY_CI
    AND uah.resource_person_primary_flag = 'Y'
  GROUP BY uah.resource_person_id
"""

case_owner_ima = """
  SELECT
    REPLACE(xa.assignee_uref, 'WUA') wua_id
    , bad.ima_id
  FROM (
    SELECT
      MAX(bad.id) bad_id
      , bas.ima_id
    FROM bpmmgr.business_assignment_details bad
    INNER JOIN (
      SELECT bra.bas_id, REPLACE(xbc.primary_data_uref, 'IMA') ima_id
      FROM bpmmgr.xview_business_contexts xbc
      INNER JOIN bpmmgr.business_routine_contexts brc ON xbc.bc_id = brc.bc_id
      INNER JOIN bpmmgr.business_stages bs ON bs.brc_id = brc.id AND bs.end_datetime IS NULL
      INNER JOIN bpmmgr.business_routine_assignments bra ON bra.brc_id = brc.id
      INNER JOIN bpmmgr.xview_bpd_action_set_assigns xbasa ON xbasa.bpd_id = bs.bp_id
        AND xbasa.stage_label = bs.stage_label
        AND xbasa.assignment = bra.assignment
        AND xbasa.workbasket = 'WORK'
      WHERE  bs.stage_label LIKE 'IMA%'
        AND bra.assignment = 'CASE_OFFICER'
      ) bas on bas.bas_id = bad.bas_id
    GROUP BY bas.ima_id
    ) bad
  INNER JOIN bpmmgr.xview_assignees xa ON xa.bad_id = bad.bad_id
"""

case_owner_ca = """
  SELECT
    REPLACE(xa.assignee_uref, 'WUA') wua_id
    , bad.ca_id
  FROM (
    SELECT
      MAX(bad.id) bad_id
      , bas.ca_id
    FROM bpmmgr.business_assignment_details bad
    INNER JOIN (
      SELECT bra.bas_id, REPLACE(xbc.primary_data_uref, 'CA') ca_id
      FROM bpmmgr.xview_business_contexts xbc
      INNER JOIN bpmmgr.business_routine_contexts brc ON xbc.bc_id = brc.bc_id
      INNER JOIN bpmmgr.business_stages bs ON bs.brc_id = brc.id AND bs.end_datetime IS NULL
      INNER JOIN bpmmgr.business_routine_assignments bra ON bra.brc_id = brc.id
      INNER JOIN bpmmgr.xview_bpd_action_set_assigns xbasa ON xbasa.bpd_id = bs.bp_id
        AND xbasa.stage_label = bs.stage_label
        AND xbasa.assignment = bra.assignment
        AND xbasa.workbasket = 'WORK'
      WHERE  bs.stage_label LIKE 'CA%'
        AND bra.assignment = 'CASE_OFFICER'
      ) bas on bas.bas_id = bad.bas_id
    GROUP BY bas.ca_id
    ) bad
  INNER JOIN bpmmgr.xview_assignees xa ON xa.bad_id = bad.bad_id
"""
