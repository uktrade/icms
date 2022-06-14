# TODO ICMSLST-1493: Investigate case_owner_id
# TODO ICMSLST-1493: Find issue paper licence only
# TODO ICMSLST-1498: User fields need updating when user data is migrated
# TODO ICMSLST-1493: Determine if process is active from data

# xiad.submitted_by_wua_id submitted_by_id
# xiad.created_by_wua_id created_by_id
# xiad.last_updated_by_wua_id last_updated_by_id
# xiad.importer_id
# xiad.importer_office_id
# xiad.agent_id
# xiad.agent_office_id
# xiad.contact_rp_id contact_id
# xiad.provided_to_imi_by_wua_id imi_submitted_by_id

import_application_base = """
SELECT
  ia.case_ref reference
  , 1 is_active
  , xiad.status
  , xiad.submitted_datetime submit_datetime
  , xiad.response_decision decision
  , xiad.refuse_reason
  , xiad.applicant_reference
  , ia.created_datetime create_datetime
  , ia.created_datetime created
  , xiad.variation_no
  , xiad.legacy_case_flag
  , xiad.chief_usage_status
  , xiad.under_appeal_flag
  , xiad.variation_decision
  , xiad.variation_refuse_reason
  , xiad.issue_date
  , xiad.licence_extended licence_extended_flag
  , ir.licence_ref licence_reference
  , xiad.last_updated_datetime last_update_datetime
  , 2 submitted_by_id
  , 2 created_by_id
  , 2 last_updated_by_id
  , 2 importer_id
  , 2 importer_office_id
  , 2 agent_id
  , 2 agent_office_id
  , 2 contact_id
  , xiad.coo_country_id origin_country_id
  , xiad.coc_country_id consignment_country_id
  , NULL imi_submitted_by_id
  , xiad.date_provided_to_imi imi_submit_datetime
  , iat.id application_type_id
  , '{process_type}' process_type
  , ia_details.*
FROM
  impmgr.xview_ima_details xiad
INNER JOIN impmgr.import_applications ia ON ia.id = xiad.ima_id
INNER JOIN impmgr.import_application_types iat
  ON iat.ima_type = xiad.ima_type AND iat.ima_sub_type = xiad.ima_sub_type
INNER JOIN ({subquery}) ia_details ON ia_details.ima_id = xiad.ima_id
LEFT JOIN impmgr.ima_responses ir ON ir.ima_id = xiad.ima_id AND ir.licence_ref IS NOT NULL
WHERE
  xiad.ima_type = '{ima_type}'
  AND xiad.IMA_SUB_TYPE = '{ima_sub_type}'
  AND xiad.status_control = 'C'
"""

import_checklist_base = """
SELECT cl.*
FROM impmgr.xview_ima_details xiad
INNER JOIN (
  SELECT
    ad.id imad_id, x.*
  FROM impmgr.import_application_details ad,
    XMLTABLE('/*'
    PASSING ad.xml_data
    COLUMNS
      case_update VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_UPDATE_REQUIRED/text()'
      , fir_required VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_FIR_REQUIRED/text()'
      , response_preparation VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_DECISION_RESPONSE/text()'
      , validity_period_correct VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_VALIDITY_PERIOD/text()'
      , endorsements_listed VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_ENDORSEMENTS/text()'
      , authorisation VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_AUTHORISATION/text()'
      {columns}
    ) x
    WHERE status_control = 'C'
  ) cl ON cl.imad_id = xiad.imad_id
WHERE
  xiad.ima_type = '{ima_type}'
  AND xiad.IMA_SUB_TYPE = '{ima_sub_type}'
  AND xiad.status_control = 'C'
  AND xiad.submitted_datetime IS NOT NULL
"""


# TODO ICMSLST-1494: Expand to cover all application types
# TODO ICMSLST-1494: Find how to determine if paper only

import_application_licence = """
SELECT
  imad_id
  , created_datetime
  , CASE licence_validity WHEN 'CURRENT' THEN 'AC' ELSE 'AR' END status
  , licence_start_date
  , licence_end_date
FROM impmgr.ima_responses ir
INNER JOIN impmgr.ima_response_details ird ON ird.ir_id = ir.id
INNER JOIN impmgr.import_application_details iad ON iad.id = ird.imad_id
WHERE response_type = 'TEX_QUOTA_LICENCE'
AND iad.status_control = 'C'
"""
