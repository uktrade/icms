cfs_application = """
WITH rp_wua AS (
  SELECT uah.resource_person_id
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
), case_owner AS (
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
)
SELECT
  xcad.ca_id
  , xcad.status
  , xcad.submitted_datetime submit_datetime
  , ca.case_reference reference
  , xcad.case_decision decision
  , xcad.refuse_reason
  , xcad.last_updated_datetime last_update_datetime
  , last_updated_by_wua_id last_updated_by_id
  , xcad.variation_number variation_no
  , xcad.submitted_by_wua_id submitted_by_id
  , ca.created_datetime created
  , xcad.created_by_wua_id created_by_id
  , xcad.exporter_id
  , xcad.exporter_office_id
  , rp_wua.wua_id contact_id
  , xcad.agent_id
  , xcad.agent_office_id
  , 'CertificateOfFreeSaleApplication' process_type
  , cat.id application_type_id
  , case_owner.wua_id case_owner_id
  , cad.*
FROM impmgr.xview_certificate_app_details xcad
  INNER JOIN impmgr.certificate_applications ca ON ca.id = xcad.ca_id
  INNER JOIN impmgr.certificate_application_types cat ON cat.ca_type = xcad.application_type
  INNER JOIN (
  SELECT cad.id cad_id, x.*
  FROM impmgr.certificate_app_details cad,
    XMLTABLE('/*'
    PASSING cad.xml_data
    COLUMNS
      case_note_xml XMLTYPE PATH '/CA/CASE/NOTES/NOTE_LIST'
      , fir_xml XMLTYPE PATH '/CA/CASE/RFIS/RFI_LIST'
      , update_request_xml XMLTYPE PATH '/CA/CASE/APPLICATION_UPDATES/UPDATE_LIST'
      , variations_xml XMLTYPE PATH '/CA/CASE/VARIATIONS/VARIATION_LIST'
      , withdrawal_xml XMLTYPE PATH '/CA/CASE/APPLICATION_WITHDRAWALS/WITHDRAWAL_LIST'
    ) x
  ) cad on cad.cad_id = xcad.cad_id
  LEFT JOIN rp_wua ON rp_wua.resource_person_id = xcad.contact_rp_id
  LEFT JOIN case_owner ON case_owner.ca_id = xcad.ca_id
WHERE xcad.status_control = 'C'
  AND xcad.application_type = 'CFS'
  AND xcad.status <> 'DELETED'
  AND (xcad.status <> 'IN_PROGRESS' OR xcad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""

cfs_schedule = """
SELECT
  xcas.ca_id
  , xcas.cad_id
  , xcas.schedule_ordinal
  , CASE xcas.manufacturer_status
    WHEN 'IS_MANUFACTURER' THEN 'MANUFACTURER'
    WHEN 'IS_NOT_MANUFACTURER' THEN 'NOT_MANUFACTURER'
  END exporter_status
  , schedules.brand_name_holder
  , schedules.product_eligibility
  , schedules.goods_placed_on_uk_market
  , schedules.goods_export_only
  , schedules.any_raw_materials
  , schedules.final_product_end_use
  , CASE st_gmp.statement WHEN NULL THEN 0 ELSE 1 END accordance_with_standards
  , CASE st_rp.statement WHEN NULL THEN 0 ELSE 1 END is_responsible_person
  , xcas.manufactured_at_name manufacturer_name
  , schedules.manufacturer_address_type
  , xcas.manufactured_at_postcode manufacturer_postcode
  , xcas.manufactured_at_address manufacturer_address
  , xcas.country_of_manufacture country_of_manufacture_id
  , xcas.created_by_wua_id created_by_id
  , xcas.start_datetime created_at
  , xcas.last_updated_datetime updated_at
  , schedules.legislation_xml
  , schedules.product_xml
FROM impmgr.xview_certificate_app_details xcad
INNER JOIN impmgr.xview_cert_app_schedules xcas ON xcas.cad_id = xcad.cad_id
INNER JOIN (
  SELECT
    cad.id cad_id
    , x.schedule_ordinal
    , CASE x.brand_name_holder WHEN 'true' THEN 'yes' WHEN 'false' THEN 'no' ELSE NULL END brand_name_holder
    , x.eligibility product_eligibility
    , CASE x.uk_market WHEN 'true' THEN 'yes' WHEN 'false' THEN 'no' ELSE NULL END goods_placed_on_uk_market
    , CASE x.export_only WHEN 'true' THEN 'yes' WHEN 'false' THEN 'no' ELSE NULL END goods_export_only
    , CASE x.any_raw_materials WHEN 'true' THEN 'yes' WHEN 'false' THEN 'no' ELSE NULL END any_raw_materials
    , x.final_product_end_use
    , CASE x.manufacturer_address_type WHEN 'SEARCH' THEN 'SEARCH' ELSE 'MANUAL' END manufacturer_address_type
    , XMLTYPE.getClobVal(legislation_xml) legislation_xml
    , XMLTYPE.getClobVal(product_xml) product_xml
  FROM
    impmgr.certificate_app_details cad
    CROSS JOIN XMLTABLE('/CA/APPLICATION/PRODUCTS/SCHEDULE_LIST/*'
    PASSING cad.xml_data
    COLUMNS
      schedule_ordinal FOR ORDINALITY
      , eligibility VARCHAR2(20) PATH '/SCHEDULE/ELIGIBILITY[not(fox-error)]/text()'
      , brand_name_holder VARCHAR2(5) PATH '/SCHEDULE/BRAND_NAME_STATUS[not(fox-error)]/text()'
      , export_only VARCHAR2(5) PATH '/SCHEDULE/IS_EU_MARKET[not(fox-error)]/text()'
      , uk_market VARCHAR2(5) PATH '/SCHEDULE/IS_NEVER_EU_MARKET[not(fox-error)]/text()'
      , any_raw_materials VARCHAR2(5) PATH '/SCHEDULE/RAW_MATERIALS_EXIST[not(fox-error)]/text()'
      , final_product_end_use VARCHAR2(4000) PATH '/SCHEDULE/END_USE[not(fox-error)]/text()'
      , manufacturer_address_type VARCHAR2(4000) PATH '/SCHEDULE/MANUFACTURED_AT/ENTRY_TYPE[not(fox-error)]/text()'
      , legislation_xml XMLTYPE PATH '/SCHEDULE/LEGISLATION_LIST'
      , product_xml XMLTYPE PATH '/SCHEDULE/PRODUCT_LIST'
    ) x
  ) schedules ON schedules.cad_id = xcas.cad_id AND schedules.schedule_ordinal = xcas.schedule_ordinal
LEFT JOIN
  impmgr.xview_cert_app_schd_statements st_rp
    ON st_rp.cad_id = xcas.cad_id
    AND st_rp.schedule_ordinal = xcas.schedule_ordinal
    AND st_rp.statement IN ('EU_COSMETICS_RESPONSIBLE_PERSON', 'EU_COSMETICS_RESPONSIBLE_PERSON_NI')
LEFT JOIN
  impmgr.xview_cert_app_schd_statements st_gmp
    ON st_gmp.cad_id = xcas.cad_id
    AND st_gmp.schedule_ordinal = xcas.schedule_ordinal
    AND st_gmp.statement IN ('GOOD_MANUFACTURING_PRACTICE', 'GOOD_MANUFACTURING_PRACTICE_NI')
WHERE xcad.status_control = 'C'
  AND xcad.application_type = 'CFS'
  AND xcad.status <> 'DELETED'
  AND (xcad.status <> 'IN_PROGRESS' OR xcad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
ORDER BY xcas.cad_id, xcas.schedule_ordinal
"""

hse_emails = """
SELECT
  e.ca_id
  , CASE e.email_status WHEN 'DELETED' THEN 0 ELSE 1 END is_active
  , e.email_status status
  , r.email_address  "to"
  , e.email_subject subject
  , e.email_body body
  , e.response_body response
  , e.start_datetime sent_datetime
  , CASE e.email_status WHEN 'CLOSED' THEN e.last_updated_datetime ELSE NULL END closed_datetime
  , 'CA_HSE_EMAIL' template_code
FROM impmgr.xview_cert_app_hse_emails e
INNER JOIN impmgr.hse_email_recipients r ON r.status = 'CURRENT'
WHERE e.status_control = 'C'
AND e.status <> ' DELETED'
ORDER BY e.cad_id, e.email_id
"""


cfs_schedule_timestamp_update = """
UPDATE web_cfsschedule SET created_at = data_migration_cfsschedule.created_at
FROM data_migration_cfsschedule
WHERE web_cfsschedule.id = data_migration_cfsschedule.id
"""
