__all__ = [
    "export_application_type",
    "export_application_countries",
    "export_certificate",
    "export_certificate_docs",
]

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
AND xcac.status <> 'DELETED'
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
  , cad.*
FROM impmgr.xview_certificate_app_details xcad
INNER JOIN impmgr.certificate_applications ca ON ca.id = xcad.ca_id
INNER JOIN impmgr.certificate_application_types cat ON cat.ca_type = xcad.application_type
INNER JOIN (
{application_details}
) cad on cad.cad_id = xcad.cad_id
WHERE xcad.status_control = 'C'
AND xcad.application_type = '{application_type}'
AND xcad.status <> 'DELETED'
"""


export_certificate = """
SELECT
  car.ca_id
  , card.cad_id
  , card.issue_datetime case_completion_datetime
  , CASE card.status
    WHEN 'DRAFT' THEN 'DR'
    WHEN 'DELETED' THEN 'AR'
    ELSE 'AC'
    END status
  , CASE
    WHEN cad.variation_number > 0
    THEN ca.case_reference || '/' || cad.variation_number
    ELSE ca.case_reference
  END case_reference
  , card.start_datetime created_at
  , card.last_updated_datetime updated_at
FROM impmgr.certificate_app_responses car
  INNER JOIN impmgr.cert_app_response_details card ON card.car_id = car.id
  INNER JOIN impmgr.certificate_applications ca ON ca.id = car.ca_id
  INNER JOIN impmgr.certificate_app_details cad ON cad.id = card.cad_id
WHERE card.status_control = 'C'
"""

export_certificate_docs = """
SELECT
  card.cad_id
  , dd.id document_legacy_id
  , cardc.certificate_reference reference
  , cardc.id certificate_id
  , 'CERTIFICATE' document_type
  , cardc.country_id
  , xdd.title filename
  , xdd.content_type
  , dbms_lob.getlength(sld.blob_data) file_size
  , sld.id || '-' || xdd.title path
  , dd.created_datetime
  , 2 created_by_id
FROM impmgr.certificate_app_responses car
  INNER JOIN impmgr.cert_app_response_details card ON card.car_id = car.id
  INNER JOIN impmgr.cert_app_response_detail_certs cardc ON cardc.card_id = card.id
  INNER JOIN decmgr.xview_document_data xdd ON xdd.di_id = cardc.document_instance_id AND xdd.system_document = 'N' AND xdd.content_description = 'PDF'
  INNER JOIN decmgr.document_data dd ON dd.id = xdd.dd_id
  INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(dd.secure_lob_ref).id
WHERE card.status_control = 'C'
ORDER BY cardc.id
"""
