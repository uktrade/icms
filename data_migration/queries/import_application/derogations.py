from web.flow.models import ProcessTypes

from .import_application import (
    common_xml_fields,
    import_application_base,
    import_checklist_base,
)

__all__ = ["derogations_application", "derogations_checklist"]


derogations_application_subquery = """
  SELECT
    ad.ima_id, ad.id imad_id, x.*
  FROM impmgr.import_application_details ad
  CROSS JOIN XMLTABLE('/*'
    PASSING ad.xml_data
    COLUMNS
      contract_sign_date VARCHAR2(4000) PATH '/IMA/APP_DETAILS/SAN_DETAILS/CONTRACT_SIGN_DATE[not(fox-error)]/text()'
      , contract_completion_date VARCHAR2(4000) PATH '/IMA/APP_DETAILS/SAN_DETAILS/CONTRACT_COMPLETE_DATE[not(fox-error)]/text()'
      , explanation VARCHAR2(4000) PATH '/IMA/APP_DETAILS/SAN_DETAILS/CONTRACT_DETAILS[not(fox-error)]/text()'
      , commodity_id VARCHAR2(100) PATH '/IMA/APP_DETAILS/SAN_DETAILS/COMMODITY_LIST/COMMODITY/COMMODITY_ID[not(fox-error)]/text()'
      , goods_description VARCHAR2(4000) PATH '/IMA/APP_DETAILS/SAN_DETAILS/COMMODITY_LIST/COMMODITY/COMMODITY_DESC[not(fox-error)]/text()'
      , quantity VARCHAR2(100) PATH '/IMA/APP_DETAILS/SAN_DETAILS/COMMODITY_LIST/COMMODITY/QUANTITY[not(fox-error)]/text()'
      , unit VARCHAR2(100) PATH '/IMA/APP_DETAILS/SAN_DETAILS/COMMODITY_LIST/COMMODITY/UNIT[not(fox-error)]/text()'
      , value VARCHAR2(100) PATH '/IMA/APP_DETAILS/SAN_DETAILS/COMMODITY_LIST/COMMODITY/VALUE[not(fox-error)]/text()'
      , entity_consulted_name VARCHAR2(4000) PATH '/IMA/APP_DETAILS/SAN_DETAILS/SYRIA/CONSULTANT/text()'
      , activity_benefit_anyone VARCHAR2(4000) PATH '/IMA/APP_DETAILS/SAN_DETAILS/SYRIA/EU_BENEFICIARIES/text()'
      , purpose_of_request VARCHAR2(4000) PATH '/IMA/APP_DETAILS/SAN_DETAILS/SYRIA/REQUEST_PURPOSE/text()'
      , civilian_purpose_details  VARCHAR2(4000) PATH '/IMA/APP_DETAILS/SAN_DETAILS/SYRIA/REQUEST_PURPOSE_OTHER/text()'
{common_xml_fields}
    ) x
    WHERE status_control = 'C'
""".format(
    common_xml_fields=common_xml_fields
)

derogations_checklist_columns = """
      , supporting_document_received VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/SAN_SUPPORTING_DOCS/text()'
      , sncorf_consulted VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/SNCORF_CONSULTED/text()'
      , sncorf_response_within_30_days VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/SNCORF_RESPONSE/text()'
      , beneficiaries_not_on_list VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/SYRIA_SANCTIONS/text()'
      , request_purpose_confirmed VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/SYRIA_REQUEST_PURPOSE/text()'
"""

derogations_application = import_application_base.format(
    **{
        "subquery": derogations_application_subquery,
        "ima_type": "SAN",
        "ima_sub_type": "SAN1",
        "process_type": ProcessTypes.DEROGATIONS,
    }
)

derogations_checklist = import_checklist_base.format(
    **{"columns": derogations_checklist_columns, "ima_type": "SAN", "ima_sub_type": "SAN1"}
)
