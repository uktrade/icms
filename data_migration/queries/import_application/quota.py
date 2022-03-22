from web.flow.models import ProcessTypes

from .import_application import import_application_base, import_checklist_base

wood_application_subquery = """
  SELECT
    ad.ima_id, ad.id imad_id, x.*
  FROM impmgr.import_application_details ad,
    XMLTABLE('/*'
    PASSING ad.xml_data
    COLUMNS
      shipping_year VARCHAR2(4) PATH '/IMA/APP_DETAILS/WOOD_DETAILS/YEAR/text()'
      , exporter_name VARCHAR2(4000) PATH '/IMA/APP_DETAILS/WOOD_DETAILS/EXPORTER_DETAILS/EXPORTER_NAME[not(contains(text(), "<script>alert"))]/text()'
      , exporter_address VARCHAR2(4000) PATH '/IMA/APP_DETAILS/WOOD_DETAILS/EXPORTER_DETAILS/EXPORTER_ADDRESS[not(contains(text(), "<script>alert"))]/text()'
      , exporter_vat_nr VARCHAR2(4000) PATH '/IMA/APP_DETAILS/WOOD_DETAILS/EXPORTER_DETAILS/EXPORTER_VAT_NUMBER[not(contains(text(), "<script>alert"))]/text()'
      , goods_description VARCHAR2(4000) PATH
        '/IMA/APP_DETAILS/WOOD_DETAILS/COMMODITY_LIST/COMMODITY/COMMODITY_DESC[not(contains(text(), "<script>alert"))]/text()'
      , goods_qty VARCHAR2(20) PATH '/IMA/APP_DETAILS/WOOD_DETAILS/COMMODITY_LIST/COMMODITY/QUANTITY/text()'
      , goods_unit VARCHAR2(20) PATH '/IMA/APP_DETAILS/WOOD_DETAILS/COMMODITY_LIST/COMMODITY/UNIT/text()'
      , commodity_id VARCHAR2(20) PATH '/IMA/APP_DETAILS/WOOD_DETAILS/COMMODITY_LIST/COMMODITY/COMMODITY_ID/text()'
      , additional_comments VARCHAR2(4000) PATH '/IMA/APP_DETAILS/WOOD_DETAILS/ADDITIONAL_COMMENTS[not(contains(text(), "<script>alert"))]/text()'
      , contract_files_xml XMLTYPE PATH '/IMA/APP_DETAILS/WOOD_DETAILS/CONTRACT_LIST'
      , export_certs_xml XMLTYPE PATH '/IMA/APP_DETAILS/WOOD_DETAILS/EXPORT_CERTIFICATE_LIST'
      , cover_letter VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/RESPONSE/APPROVE/COVER_LETTER/text()'
    ) x
  WHERE status_control = 'C'
"""

wood_checklist_columns = """
  , sigl_wood_application_logged VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/SIGL/SIGL_FLAG/text()'
"""

wood_application = import_application_base.format(
    **{
        "subquery": wood_application_subquery,
        "ima_type": "WD",
        "ima_sub_type": "QUOTA",
        "process_type": ProcessTypes.WOOD,
    }
)
wood_checklist = import_checklist_base.format(
    **{"columns": wood_checklist_columns, "ima_type": "WD", "ima_sub_type": "QUOTA"}
)


# TODO ICMSLST-1493: Find category_licence_description
textiles_application_subquery = """
  SELECT
    ad.ima_id, ad.id imad_id, x.*
  FROM impmgr.import_application_details ad,
    XMLTABLE('/*'
    PASSING ad.xml_data
    COLUMNS
      goods_cleared VARCHAR2(5) PATH '/IMA/APP_DETAILS/TEX_DETAILS/GOODS_CLEARED/text()'
      , category_commodity_group_id VARCHAR2(4000) PATH '/IMA/APP_DETAILS/TEX_DETAILS/COMMODITY_GROUP/text()'
      , commodity_id VARCHAR2(4000) PATH '/IMA/APP_DETAILS/TEX_DETAILS/COMMODITY_LIST/COMMODITY/COMMODITY_ID/text()'
      , contract_files_xml XMLTYPE PATH '/IMA/APP_DETAILS/WOOD_DETAILS/CONTRACT_LIST/*'
      , cover_letter VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/RESPONSE/APPROVE/COVER_LETTER/text()'
      , goods_description VARCHAR2(4000) PATH '/IMA/APP_DETAILS/TEX_DETAILS/COMMODITY_LIST/COMMODITY/COMMODITY_DESC/text()'
      , quantity VARCHAR2(4000) PATH '/IMA/APP_DETAILS/TEX_DETAILS/COMMODITY_LIST/COMMODITY/QUANTITY/text()'
      , shipping_year VARCHAR2(4) PATH '/IMA/APP_DETAILS/TEX_DETAILS/YEAR/text()'
    ) x
  WHERE status_control = 'C'
"""

textiles_checklist_columns = """
  , within_maximum_amount_limit VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/TEX_CHECK_AMOUNTS/text()'
"""

textiles_application = import_application_base.format(
    **{
        "subquery": textiles_application_subquery,
        "ima_type": "TEX",
        "ima_sub_type": "QUOTA",
        "process_type": ProcessTypes.TEXTILES,
    }
)
textiles_checklist = import_checklist_base.format(
    **{"columns": textiles_checklist_columns, "ima_type": "TEX", "ima_sub_type": "QUOTA"}
)
