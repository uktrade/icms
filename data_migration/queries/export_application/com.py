from .export import export_application_base

__all__ = ["com_application"]

com_subquery = """
INNER JOIN (
  SELECT
    cad.id cad_id
    , CASE x.is_pesticide_on_free_sale_uk WHEN 'true' THEN 1 WHEN 'false' THEN 0 ELSE NULL END is_pesticide_on_free_sale_uk
    , CASE x.is_manufacturer WHEN 'true' THEN 1 WHEN 'false' THEN 0 ELSE NULL END is_manufacturer
    , x.product_name
    , x.chemical_name
    , x.manufacturing_process
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
    ) x
) cad on cad.cad_id = xcad.cad_id
"""

com_application = export_application_base.format(
    **{
        "process_type": "CertificateOfManufactureApplication",
        "cad": ", cad.*",
        "application_details": com_subquery,
        "application_type": "COM",
    }
)
