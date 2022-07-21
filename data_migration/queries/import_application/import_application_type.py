__all__ = ["ia_type", "usage"]

ia_type = """
SELECT
  id
  , status
  , ima_type type
  , ima_sub_type sub_type
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
  , declaration_template_mnem
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
WHERE iat.ima_type <> 'GS'
AND xcgu.country_id IS NOT NULL
"""
