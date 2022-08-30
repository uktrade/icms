from .export import export_application_base

__all__ = ["cfs_application", "cfs_schedule"]

cfs_subquery = """
  SELECT cad.id cad_id
  FROM impmgr.certificate_app_details cad
"""

cfs_application = export_application_base.format(
    **{
        "process_type": "CertificateOfFreeSaleApplication",
        "application_details": cfs_subquery,
        "application_type": "CFS",
    }
)

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
  , 2 created_by_id
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
    impmgr.certificate_app_details cad,
    XMLTABLE('/CA/APPLICATION/PRODUCTS/SCHEDULE_LIST/*'
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
ORDER BY xcas.cad_id, xcas.schedule_ordinal
"""
