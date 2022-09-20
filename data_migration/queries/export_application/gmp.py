from .export import common_xml_fields, export_application_base

__all__ = ["gmp_application", "beis_emails"]

gmp_subquery = """
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
      , {common_xml_fields}
    ) x
""".format(
    common_xml_fields=common_xml_fields
)

gmp_application = export_application_base.format(
    **{
        "process_type": "CertificateofGoodManufacturingPractice",
        "application_details": gmp_subquery,
        "application_type": "GMP",
    }
)


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
