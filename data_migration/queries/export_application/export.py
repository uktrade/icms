__all__ = ["export_application_type", "export_application_countries", "gmp"]

export_application_type = """
SELECT
  id
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , ca_type type_code
  , ca_type_title type
  , CASE allow_multiple_products WHEN 'true' THEN 1 ELSE 0 END allow_multiple_products
  , CASE generate_cover_letter WHEN 'true' THEN 1 ELSE 0 END generate_cover_letter
  , CASE allow_hse_authorization WHEN 'true' THEN 1 ELSE 0 END allow_hse_authorization
  , country_group_id country_group_legacy_id
  , country_of_manufacture_cg_id
FROM impmgr.certificate_application_types
"""


export_application_countries = """
SELECT xcac.cad_id, xcac.country_id
FROM impmgr.xview_cert_app_countries xcac
INNER JOIN impmgr.xview_certificate_app_details xcad ON xcad.cad_id = xcac.cad_id
WHERE xcac.status_control = 'C'
AND xcad.application_type = 'GMP'
"""


export_application_base = """
SELECT
  xcad.ca_id
  , xcad.status
  , xcad.submitted_datetime submit_datetime
  , ca.case_reference reference
  , xcad.case_decision decision
  , xcad.refuse_reason
  , xcad.last_updated_datetime last_update_datetime
  , 2 last_updated_by_id
  , xcad.variation_number variation_no
  , 2 submitted_by_id
  , 2 created_by_id
  , xcad.exporter_id
  , xcad.exporter_office_id
  , 2 contact_id
  , xcad.agent_id
  , xcad.agent_office_id
  , '{process_type}' process_type
  , cat.id application_type_id
  {cad}
FROM impmgr.xview_certificate_app_details xcad
INNER JOIN impmgr.certificate_applications ca ON ca.id = xcad.ca_id
INNER JOIN impmgr.certificate_application_types cat ON cat.ca_type = xcad.application_type
{application_details}
WHERE xcad.status_control = 'C'
AND xcad.application_type = '{application_type}'
AND xcad.status <> 'DELETED'
"""


gmp_subquery = """
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
    ) x
) cad ON cad.cad_id = xcad.cad_id
""".strip()

gmp = export_application_base.format(
    **{
        "process_type": "CertificateofGoodManufacturingPractice",
        "cad": ", cad.*",
        "application_details": gmp_subquery,
        "application_type": "GMP",
    }
)
