gmp_application = """
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
        AND sub.account_statuS = 'ACTIVE'
    )
    ELSE MAX(wua_id)
  END wua_id
  FROM SECUREMGR.WEB_USER_ACCOUNT_HISTORIES uah
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
  , 'CertificateofGoodManufacturingPractice' process_type
  , cat.id application_type_id
  , case_owner.wua_id case_owner_id
  , cad.*
FROM impmgr.xview_certificate_app_details xcad
  INNER JOIN impmgr.certificate_applications ca ON ca.id = xcad.ca_id
  INNER JOIN impmgr.certificate_application_types cat ON cat.ca_type = xcad.application_type
  INNER JOIN (
  SELECT
    cad.id cad_id
    , brand_name
    , CASE is_responsible_person WHEN 'true' THEN 'yes' WHEN 'false' THEN 'no' ELSE NULL END is_responsible_person
    , CASE is_manufacturer WHEN 'true' THEN 'yes' WHEN 'false' THEN 'no' ELSE NULL END is_manufacturer
    , CASE auditor_accredited WHEN 'true' THEN 'yes' WHEN 'false' THEN 'no' ELSE NULL END auditor_accredited
    , CASE auditor_certified WHEN 'true' THEN 'yes' WHEN 'false' THEN 'no' ELSE NULL END auditor_certified
    , responsible_person_name
    , responsible_address_type
    , responsible_person_postcode
    , responsible_person_address
    , responsible_person_country
    , manufacturer_name
    , manufacturer_address_type
    , manufacturer_postcode
    , manufacturer_address
    , manufacturer_country
    , gmp_certificate_issued
    , file_folder_id
    , case_note_xml
    , XMLTYPE.getClobVal(x.variations_xml) variations_xml
  FROM
    impmgr.certificate_app_details cad,
    XMLTABLE('/*'
    PASSING cad.xml_data
    COLUMNS
      brand_name VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/BRAND_DETAILS/BRAND_NAME[not(fox-error)]/text()'
      , is_responsible_person VARCHAR(5) PATH '/CA/APPLICATION/GMP_DETAILS/RESPONSIBLE_ADDRESS_DETAILS/RESPONSIBLE_PERSON_FLAG[not(fox-error)]/text()'
      , is_manufacturer VARCHAR(5) PATH '/CA/APPLICATION/GMP_DETAILS/MANUFACTURER_ADDRESS_DETAILS/MANUFACTURER_FLAG[not(fox-error)]/text()'
      , auditor_accredited VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/GMP_DOCUMENTS/ISO_17021_DOCUMENT[not(fox-error)]/text()'
      , auditor_certified VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/GMP_DOCUMENTS/ISO_17065_DOCUMENT[not(fox-error)]/text()'
      , responsible_person_name VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/RESPONSIBLE_ADDRESS_DETAILS/NAME[not(fox-error)]/text()'
      , responsible_address_type VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/RESPONSIBLE_ADDRESS_DETAILS/ADDRESS_ENTRY_TYPE[not(fox-error)]/text()'
      , responsible_person_postcode VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/RESPONSIBLE_ADDRESS_DETAILS/POSTCODE[not(fox-error)]/text()'
      , responsible_person_address VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/RESPONSIBLE_ADDRESS_DETAILS/ADDRESS[not(fox-error)]/text()'
      , responsible_person_country VARCHAR(2) PATH '/CA/APPLICATION/GMP_DETAILS/RESPONSIBLE_ADDRESS_DETAILS/RESPONSIBLE_PERSON_COUNTRY[not(fox-error)]/text()'
      , manufacturer_name VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/MANUFACTURER_ADDRESS_DETAILS/NAME[not(fox-error)]/text()'
      , manufacturer_address_type VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/MANUFACTURER_ADDRESS_DETAILS/ADDRESS_ENTRY_TYPE[not(fox-error)]/text()'
      , manufacturer_postcode VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/MANUFACTURER_ADDRESS_DETAILS/POSTCODE[not(fox-error)]/text()'
      , manufacturer_address VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/MANUFACTURER_ADDRESS_DETAILS/ADDRESS[not(fox-error)]/text()'
      , manufacturer_country VARCHAR(10) PATH '/CA/APPLICATION/GMP_DETAILS/MANUFACTURER_ADDRESS_DETAILS/COUNTRY_OF_MANUFACTURE[not(fox-error)]/text()'
      , gmp_certificate_issued VARCHAR(4000) PATH '/CA/APPLICATION/GMP_DETAILS/GMP_DOCUMENTS/MAIN_DOCUMENT_CERTIFICATE[not(fox-error)]/text()'
      , file_folder_id INTEGER PATH '/CA/APPLICATION/FILE_FOLDER_ID/text()'
      , case_note_xml XMLTYPE PATH '/CA/CASE/NOTES/NOTE_LIST'
      , fir_xml XMLTYPE PATH '/CA/CASE/RFIS/RFI_LIST'
      , update_request_xml XMLTYPE PATH '/CA/CASE/APPLICATION_UPDATES/UPDATE_LIST'
      , variations_xml XMLTYPE PATH '/CA/CASE/VARIATIONS/VARIATION_LIST'
    ) x
  ) cad on cad.cad_id = xcad.cad_id
  LEFT JOIN rp_wua ON rp_wua.resource_person_id = xcad.contact_rp_id
  LEFT JOIN case_owner ON case_owner.ca_id = xcad.ca_id
WHERE xcad.status_control = 'C'
  AND xcad.application_type = 'GMP'
  AND xcad.status <> 'DELETED'
  AND (
    (xcad.submitted_datetime IS NOT NULL AND ca.case_reference IS NOT NULL)
    OR xcad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY
  )
"""

beis_emails = """
SELECT
  e.ca_id
  , CASE e.email_status WHEN 'DELETED' THEN 0 ELSE 1 END is_active
  , e.email_status STATUS
  , r.email_address  "to"
  , e.email_subject subject
  , e.email_body "body"
  , e.response_body response
  , e.start_datetime sent_datetime
  , CASE e.email_status WHEN 'CLOSED' THEN e.last_updated_datetime ELSE NULL END closed_datetime
FROM impmgr.xview_cert_app_beis_emails e
INNER JOIN impmgr.beis_email_recipients r ON r.status = 'CURRENT'
WHERE e.status_control = 'C'
AND e.status <> ' DELETED'
ORDER BY e.cad_id, e.email_id
"""
