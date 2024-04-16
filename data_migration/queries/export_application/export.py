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
SELECT
  xcac.cad_id
  , xcac.country_id
FROM impmgr.xview_cert_app_countries xcac
  INNER JOIN impmgr.xview_certificate_app_details xcad ON xcad.cad_id = xcac.cad_id
WHERE xcac.status_control = 'C'
  AND xcac.status <> 'DELETED'
  AND (xcad.status <> 'IN_PROGRESS' OR xcad.last_updated_datetime > CURRENT_DATE - INTERVAL '14' DAY)
"""


export_certificate = """
SELECT
  car.ca_id
  , card.cad_id
  , card.issue_datetime case_completion_datetime
  , CASE
    WHEN card.status = 'DRAFT' THEN 'DR'
    WHEN cad_c.status = 'REVOKED' THEN 'RE'
    WHEN card.is_last_issued = 'false' THEN 'AR'
    ELSE 'AC'
    END status
  , CASE
    WHEN cad.variation_number > 0
    THEN ca.case_reference || '/' || cad.variation_number
    ELSE ca.case_reference
  END case_reference
  , card.start_datetime created_at
  , card.last_updated_datetime updated_at
  , dp.dp_id document_pack_id
FROM impmgr.certificate_app_responses car
  INNER JOIN impmgr.cert_app_response_details card ON card.car_id = car.id
  INNER JOIN impmgr.certificate_applications ca ON ca.id = car.ca_id
  INNER JOIN impmgr.certificate_app_details cad ON cad.id = card.cad_id
  INNER JOIN impmgr.certificate_app_details cad_c ON cad_c.ca_id = car.ca_id AND cad_c.status_control = 'C'
  LEFT JOIN decmgr.xview_document_packs dp ON dp.ds_id = card.document_set_id
WHERE card.status <> 'DELETED'
ORDER BY card.id
"""


export_certificate_docs = """
SELECT
  card.cad_id
  , dd.id document_legacy_id
  , SUBSTR(cardc.certificate_reference, 1, 3) prefix
  , SUBSTR(cardc.certificate_reference, 5, 4) year
  , cardc.xseq_value reference_no
  , cardc.certificate_reference reference
  , cardc.id certificate_id
  , 'CERTIFICATE' document_type
  , cardc.country_id
  , cardc.certificate_code check_code
  , xdd.title || '.pdf' filename
  , xdd.content_type
  , dbms_lob.getlength(sld.blob_data) file_size
  , 'export_certificate/' || sld.id || '-' || xdd.title || '.pdf' path
  , dd.created_datetime
  , created_by_wua_id created_by_id
  , sld.blob_data
  , sld.id AS secure_lob_ref_id
FROM impmgr.certificate_app_responses car
  INNER JOIN impmgr.cert_app_response_details card ON card.car_id = car.id
  INNER JOIN impmgr.cert_app_response_detail_certs cardc ON cardc.card_id = card.id
  INNER JOIN decmgr.xview_document_data xdd ON xdd.di_id = cardc.document_instance_id AND xdd.system_document = 'N' AND xdd.content_description = 'PDF'
  INNER JOIN decmgr.document_data dd ON dd.id = xdd.dd_id
  INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(dd.secure_lob_ref).id
WHERE sld.id > :secure_lob_ref_id
ORDER BY sld.id
"""

export_document_pack_acknowledged = """
SELECT
  xn.dp_id exportcertificate_id
  , x.user_id
FROM decmgr.xview_notifications xn
  INNER JOIN decmgr.notifications n ON n.id = xn.n_id
  INNER JOIN decmgr.xview_document_packs dp ON dp.dp_id = xn.dp_id
  INNER JOIN impmgr.cert_app_response_details card ON card.document_set_id = dp.ds_id
  CROSS JOIN XMLTABLE('/*'
    PASSING n.xml_data
    COLUMNS
      user_id INTEGER PATH '/ACKNOWLEDGEMENT/AUDIT_LIST/AUDIT/ACTION_BY_WUA_ID/text()'
  ) x
WHERE xn.acknowledgement_status = 'ACKNOWLEDGED'
"""


export_certificate_doc_max_ref = """
SELECT MAX(xseq_value)
FROM impmgr.cert_app_response_detail_certs
WHERE certificate_reference LIKE :like_match
"""


export_certificate_timestamp_update = """
UPDATE web_exportapplicationcertificate SET created_at = dm_eac.created_at, updated_at = dm_eac.updated_at
FROM data_migration_exportapplicationcertificate dm_eac
WHERE web_exportapplicationcertificate.id = dm_eac.id
"""
