from data_migration.queries.utils import case_owner_ca, rp_wua

com_application = f"""
WITH rp_wua AS ({rp_wua}), case_owner AS ({case_owner_ca})
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
  , CASE WHEN xcad.exporter_id IS NULL THEN NULL ELSE 'e-' || xcad.exporter_id || '-' || xcad.exporter_office_id END exporter_office_legacy_id
  , rp_wua.wua_id contact_id
  , xcad.agent_id
  , CASE WHEN xcad.agent_id IS NULL THEN NULL ELSE 'e-' || xcad.agent_id || '-' || xcad.agent_office_id END agent_office_legacy_id
  , 'CertificateOfManufactureApplication' process_type
  , cat.id application_type_id
  , case_owner.wua_id case_owner_id
  , cad.*
FROM impmgr.xview_certificate_app_details xcad
  INNER JOIN impmgr.certificate_applications ca ON ca.id = xcad.ca_id
  INNER JOIN impmgr.certificate_application_types cat ON cat.ca_type = xcad.application_type
  INNER JOIN (
    SELECT
      cad.id cad_id
      , CASE x.is_pesticide_on_free_sale_uk WHEN 'true' THEN 1 WHEN 'false' THEN 0 ELSE NULL END is_pesticide_on_free_sale_uk
      , CASE x.is_manufacturer WHEN 'true' THEN 1 WHEN 'false' THEN 0 ELSE NULL END is_manufacturer
      , x.product_name
      , x.chemical_name
      , x.manufacturing_process
      , x.case_note_xml
      , XMLTYPE.getClobVal(x.variations_xml) variations_xml
      , XMLTYPE.getClobVal(x.withdrawal_xml) withdrawal_xml
    FROM
      impmgr.certificate_app_details cad,
      XMLTABLE('/*'
      PASSING cad.xml_data
      COLUMNS
        is_pesticide_on_free_sale_uk VARCHAR2(5) PATH '/CA/APPLICATION//SCHEDULE/IS_DOMESTIC_MARKET_PESTICIDE[not(fox-error)]/text()'
        , is_manufacturer VARCHAR2(5) PATH '/CA/APPLICATION//SCHEDULE/IS_PESTICIDE_MANUFACTURER[not(fox-error)]/text()'
        , product_name VARCHAR2(4000) PATH '/CA/APPLICATION//SCHEDULE//PRODUCT/NAME[not(fox-error)]/text()'
        , chemical_name VARCHAR2(4000) PATH '/CA/APPLICATION//SCHEDULE//PRODUCT/CHEMICAL_NAME[not(fox-error)]/text()'
        , manufacturing_process VARCHAR2(4000) PATH '/CA/APPLICATION//SCHEDULE//PRODUCT/MANUFACTURING_PROCESS[not(fox-error)]/text()'
        , case_note_xml XMLTYPE PATH '/CA/CASE/NOTES/NOTE_LIST'
        , fir_xml XMLTYPE PATH '/CA/CASE/RFIS/RFI_LIST'
        , update_request_xml XMLTYPE PATH '/CA/CASE/APPLICATION_UPDATES/UPDATE_LIST'
        , variations_xml XMLTYPE PATH '/CA/CASE/VARIATIONS/VARIATION_LIST'
        , withdrawal_xml XMLTYPE PATH '/CA/CASE/APPLICATION_WITHDRAWALS/WITHDRAWAL_LIST'
      ) x
  ) cad on cad.cad_id = xcad.cad_id
  LEFT JOIN rp_wua ON rp_wua.resource_person_id = xcad.contact_rp_id
  LEFT JOIN case_owner ON case_owner.ca_id = xcad.ca_id
WHERE xcad.status_control = 'C'
  AND xcad.application_type = 'COM'
  AND xcad.status <> 'DELETED'
  AND (xcad.status <> 'IN_PROGRESS' OR xcad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""
