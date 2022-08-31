__all__ = ["export_application_type", "export_application_countries"]

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
