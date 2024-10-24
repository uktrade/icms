ia_type = """
SELECT
  id
  , CASE status WHEN 'CURRENT' THEN 1 ELSE 0 END is_active
  , ima_type type
  , ima_sub_type sub_type
  , CASE
   WHEN ima_sub_type_title IS NOT NULL THEN ima_type_title || ' (' || ima_sub_type_title || ')'
    ELSE ima_type_title
  END name
  , licence_type licence_type_code
  , sigl_flag
  , chief_flag
  , chief_licence_prefix
  , paper_licence_flag
  , electronic_licence_flag
  , cover_letter_flag
  , cover_letter_schedule_flag
  , category_flag
  , sigl_category_prefix
  , chief_category_prefix
  , default_licence_length_months
  , quantity_unlimited_flag
  , units_list_csv unit_list_csv
  , exp_cert_upload_flag
  , supporting_docs_upload_flag
  , multiple_commodities_flag
  , guidance_file_url
  , licence_category_description
  , use_auto_category_desc_flag usage_auto_category_desc_flag
  , case_checklist_flag
  , importer_printable
  , commodity_type commodity_type_id
  , coc_country_group_id consignment_country_group_id
  , declaration_template_mnem declaration_template_code_id
  , default_commodity_group_code default_commodity_group_id
  , master_country_group_id
  , coo_country_group_id origin_country_group_id
FROM impmgr.import_application_types iat
WHERE iat.ima_type <> 'GS'
"""


usage = """
SELECT
  rownum id
  , xcgu.start_date
  , xcgu.end_date
  , xcgu.maximum_allocation
  , xcgu.country_id
  , xcgu.cg_id commodity_group_id
  , iat.id application_type_id
FROM impmgr.xview_com_group_usages xcgu
INNER JOIN impmgr.import_application_types iat
  ON iat.ima_type = xcgu.ima_type AND iat.ima_sub_type = xcgu.ima_sub_type
INNER JOIN impmgr.commodity_group_details cgd ON cgd.cg_id = xcgu.cg_id AND cgd.status_control = 'C' AND cgd.status <> 'ARCHIVED'
WHERE iat.ima_type <> 'GS'
AND xcgu.country_id IS NOT NULL
"""
