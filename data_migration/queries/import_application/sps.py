from web.flow.models import ProcessTypes

from .import_application import common_xml_fields, import_application_base

__all__ = ["sps_application"]


sps_application_subquery = """
SELECT
  ad.ima_id, ad.id imad_id, x.*
FROM impmgr.import_application_details ad,
  XMLTABLE('/*'
  PASSING ad.xml_data
  COLUMNS
    customs_cleared_to_uk VARCHAR2(5) PATH '/IMA/APP_DETAILS/SPS_DETAILS/GOODS_CLEARED[not(fox-error)]/text()'
    , quantity VARCHAR2(100) PATH '/IMA/APP_DETAILS/SPS_DETAILS/COMMODITY_LIST/COMMODITY/QUANTITY[not(fox-error)]/text()'
    , value_gbp VARCHAR2(100) PATH '/IMA/APP_DETAILS/SPS_DETAILS/COMMODITY_LIST/COMMODITY/GBP_VALUE[not(fox-error)]/text()'
    , value_eur VARCHAR2(100) PATH '/IMA/APP_DETAILS/SPS_DETAILS/COMMODITY_LIST/COMMODITY/VALUE[not(fox-error)]/text()'
    , eur_conversion VARCHAR2(100) PATH '/IMA/APP_DETAILS/SPS_DETAILS/COMMODITY_LIST/COMMODITY/GBP_TO_EUR_CONVERSION_RATE[not(fox-error)]/text()'
    , commodity_id VARCHAR2(100) PATH '/IMA/APP_DETAILS/SPS_DETAILS/COMMODITY_LIST/COMMODITY/COMMODITY_ID[not(fox-error)]/text()'
    , file_type VARCHAR2(100) PATH '/IMA/APP_DETAILS/SPS_DETAILS/SPS_DOCUMENT_LIST/SPS_DOCUMENT/TYPE[not(fox-error)]/text()'
    , target_id VARCHAR2(100) PATH '/IMA/APP_DETAILS/SPS_DETAILS/SPS_DOCUMENT_LIST/SPS_DOCUMENT/TARGET_ID[not(fox-error)]/text()'
{common_xml_fields}
  ) x
  WHERE status_control = 'C'
""".format(
    common_xml_fields=common_xml_fields
)

sps_application = (
    import_application_base.format(
        **{
            "subquery": sps_application_subquery,
            "ima_type": "SPS",
            "ima_sub_type": "SPS1",
            "process_type": ProcessTypes.SPS,
        }
    )
    + "  AND xiad.submitted_datetime IS NOT NULL"
)
