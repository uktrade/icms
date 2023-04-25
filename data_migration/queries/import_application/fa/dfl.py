dfl_application = """
WITH rp_wua AS (
  SELECT resource_person_id, wua_id
  FROM securemgr.web_user_account_histories
  WHERE person_id_current IS NOT NULL
  AND resource_person_primary_flag = 'Y'
  GROUP BY resource_person_id, wua_id
), case_owner AS (
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
)
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
  , xiad.variation_decision
  , xiad.variation_refuse_reason
  , xiad.licence_extended licence_extended_flag
  , ir.licence_ref licence_reference
  , xiad.last_updated_datetime last_update_datetime
  , xiad.submitted_by_wua_id submitted_by_id
  , xiad.created_by_wua_id created_by_id
  , lu.id last_updated_by_id
  , xiad.importer_id
  , CASE WHEN xiad.importer_id IS NULL THEN NULL ELSE 'i-' || xiad.importer_id || '-' || xiad.importer_office_id END importer_office_legacy_id
  , xiad.agent_id
  , CASE WHEN xiad.agent_id IS NULL THEN NULL ELSE 'i-' || xiad.agent_id || '-' || xiad.agent_office_id END agent_office_legacy_id
  , rp_wua.wua_id contact_id
  , xiad.coo_country_id origin_country_id
  , xiad.coc_country_id consignment_country_id
  , xiad.provided_to_imi_by_wua_id imi_submitted_by_id
  , xiad.date_provided_to_imi imi_submit_datetime
  , iat.id application_type_id
  , 'DFLApplication' process_type
  , case_owner.wua_id case_owner_id
  , ia_details.*
FROM
  impmgr.xview_ima_details xiad
INNER JOIN impmgr.import_applications ia ON ia.id = xiad.ima_id
INNER JOIN impmgr.import_application_types iat
  ON iat.ima_type = xiad.ima_type AND iat.ima_sub_type = xiad.ima_sub_type
INNER JOIN (
SELECT
  ad.ima_id
  , ad.id imad_id
  , CASE x.proof_checked WHEN 'true' THEN 1 ELSE 0 END proof_checked
  , CASE x.deactivated_firearm WHEN 'DEACTIVATED_FIREARM' THEN 1 ELSE 0 END deactivated_firearm
  , x.commodity_code commodity_group_id
  , CASE x.know_bought_from WHEN 'Y' THEN 1 WHEN 'N' THEN 0 ELSE NULL END know_bought_from
  , x.additional_comments
  , x.fa_authorities_xml
  , XMLTYPE.getClobVal(x.bought_from_details_xml) bought_from_details_xml
  , XMLTYPE.getClobVal(x.supplementary_report_xml) supplementary_report_xml
  , CASE x.is_complete WHEN 'true' THEN 1 ELSE 0 END is_complete
  , x.no_report_reason
  , x.completed_by_id
  , TO_DATE(x.completed_datetime, 'YYYY-MM-DD') completed_datetime
  , XMLTYPE.getClobVal(XMLELEMENT("FA_GOODS_CERTS", XMLCONCAT(commodities_xml, fa_certs_xml))) fa_goods_certs_xml
  , x.file_folder_id
  , XMLTYPE.getClobVal(x.cover_letter_text) cover_letter_text
  , XMLTYPE.getClobVal(x.variations_xml) variations_xml
FROM impmgr.import_application_details ad
CROSS JOIN XMLTABLE('/*'
  PASSING ad.xml_data
  COLUMNS
    proof_checked VARCHAR2(4) PATH '/IMA/APP_DETAILS/FA_DETAILS/PROOF_MARKED_FLAG/text()'
    , deactivated_firearm VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION_LIST/SECTION[not(fox-error)]/text()'
    , commodity_code VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/COMMODITY_GROUP[not(fox-error)]/text()'
    , know_bought_from VARCHAR2(10) PATH '/IMA/APP_DETAILS/SH_DETAILS/IS_SELLER_HOLDER_PROVIDED[not(fox-error)]/text()'
    , additional_comments VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/ADDITIONAL_INFORMATION[not(fox-error)]/text()'
    , commodities_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/COMMODITY_LIST'
    , fa_certs_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/FIREARMS_CERTIFICATE_LIST'
    , fa_authorities_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/FIREARMS_AUTHORITIES/AUTHORITY_LIST'
    , bought_from_details_xml XMLTYPE PATH '/IMA/APP_DETAILS/SH_DETAILS/SELLER_HOLDER_LIST'
    , no_report_reason VARCHAR2(4000) PATH '/IMA/FA_REPORTS/NO_FIREARMS_REPORTED_DETAILS/NO_FIREARMS_REPORTED_REASON[not(fox-error)]/text()'
    , supplementary_report_xml XMLTYPE PATH '/IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST'
    , is_complete VARCHAR2(5) PATH '/IMA/FA_REPORTS/REPORT_COMPLETED_FLAG[not(fox-error)]/text()'
    , completed_by_id NUMBER PATH
      '/IMA/FA_REPORTS/HISTORICAL_REPORT_COMPLETION_LIST/HISTORICAL_REPORT_COMPLETION[last()]/REPORT_COMPLETED_BY_WUA_ID[last()]/text()'
    , completed_datetime VARCHAR(20) PATH
      '/IMA/FA_REPORTS/HISTORICAL_REPORT_COMPLETION_LIST/HISTORICAL_REPORT_COMPLETION[last()]/REPORT_COMPLETED_DATETIME[last()]/text()'
    , variations_xml XMLTYPE PATH '/IMA/APP_PROCESSING/VARIATIONS/VARIATION_REQUEST_LIST'
    , file_folder_id INTEGER PATH '/IMA/APP_METADATA/APP_DOCS_FF_ID/text()'
    , cover_letter_text XMLTYPE PATH '/IMA/APP_PROCESSING/RESPONSE/APPROVE/COVER_LETTER/*'
  ) x
WHERE status_control = 'C'
) ia_details ON ia_details.ima_id = xiad.ima_id
LEFT JOIN impmgr.ima_responses ir ON ir.ima_id = xiad.ima_id AND ir.licence_ref IS NOT NULL
LEFT JOIN decmgr.resource_people_details rp ON rp.rp_id = xiad.contact_rp_id AND rp.status_control = 'C' AND rp.status <> 'DELETED'
LEFT JOIN securemgr.web_user_accounts lu ON lu.id = xiad.last_updated_by_wua_id
LEFT JOIN rp_wua ON rp_wua.resource_person_id = xiad.contact_rp_id
LEFT JOIN case_owner ON case_owner.ima_id = xiad.ima_id
WHERE
  xiad.ima_type = 'FA'
  AND xiad.IMA_SUB_TYPE = 'DEACTIVATED'
  AND xiad.status_control = 'C'
  AND xiad.status <> 'DELETED'
  AND (
    (iat.status = 'ARCHIVED' AND xiad.submitted_datetime IS NOT NULL)
    OR (
      iat.status = 'CURRENT' AND (
        xiad.submitted_datetime IS NOT NULL OR xiad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY
      )
    )
  )
ORDER BY xiad.imad_id
"""


dfl_checklist = """
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
      , certificate_attached VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/DAF_DEACTIVATION_CERTIFICATE_ATTACHED[not(fox-error)]/text()'
      , certificate_issued VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/DAF_DEACTIVATION_CERTIFICATE_ISSUED[not(fox-error)]/text()'
    ) x
    WHERE status_control = 'C'
  ) cl ON cl.imad_id = xiad.imad_id
WHERE
  xiad.ima_type = 'FA'
  AND xiad.IMA_SUB_TYPE = 'DEACTIVATED'
  AND xiad.status_control = 'C'
  AND xiad.submitted_datetime IS NOT NULL
"""
