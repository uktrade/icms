from data_migration.queries.import_application.import_application import (
    common_xml_fields,
    import_application_base,
    import_checklist_base,
)
from web.flow.models import ProcessTypes

__all__ = ["dfl_application", "dfl_checklist"]


dfl_application_subquery = """
SELECT
  ad.ima_id
  , ad.id imad_id
  , CASE x.proof_checked WHEN 'true' THEN 1 ELSE 0 END proof_checked
  , CASE x.deactivated_firearm WHEN 'DEACTIVATED_FIREARM' THEN 1 ELSE 0 END deactivated_firearm
  , x.commodity_code commodity_group_id
  , CASE x.know_bought_from WHEN 'Y' THEN 1 WHEN 'N' THEN 0 ELSE NULL END know_bought_from
  , x.additional_comments
  , XMLTYPE.getClobVal(x.cover_letter) cover_letter
  , x.fa_authorities_xml
  , XMLTYPE.getClobVal(x.bought_from_details_xml) bought_from_details_xml
  , XMLTYPE.getClobVal(x.supplementary_report_xml) supplementary_report_xml
  , CASE x.is_complete WHEN 'true' THEN 1 ELSE 0 END is_complete
  , x.no_report_reason
  , x.completed_by_id
  , TO_DATE(x.completed_datetime, 'YYYY-MM-DD') completed_datetime
  , XMLTYPE.getClobVal(XMLELEMENT("FA_GOODS_CERTS", XMLCONCAT(commodities_xml, fa_certs_xml))) fa_goods_certs_xml
  , x.file_folder_id
FROM impmgr.import_application_details ad
CROSS JOIN XMLTABLE('/*'
  PASSING ad.xml_data
  COLUMNS
    proof_checked VARCHAR2(4) PATH '/IMA/APP_DETAILS/FA_DETAILS/PROOF_MARKED_FLAG/text()'
    , deactivated_firearm VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION_LIST/SECTION[not(fox-error)]/text()'
    , commodity_code VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/COMMODITY_GROUP[not(fox-error)]/text()'
    , know_bought_from VARCHAR2(10) PATH '/IMA/APP_DETAILS/SH_DETAILS/IS_SELLER_HOLDER_PROVIDED[not(fox-error)]/text()'
    , additional_comments VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/ADDITIONAL_INFORMATION[not(fox-error)]/text()'
    , commodities_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/COMMODITY_LIST'
    , fa_certs_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/FIREARMS_CERTIFICATE_LIST'
    , fa_authorities_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/FIREARMS_AUTHORITIES/AUTHORITY_LIST'
    , bought_from_details_xml XMLTYPE PATH '/IMA/APP_DETAILS/SH_DETAILS/SELLER_HOLDER_LIST'
    , no_report_reason VARCHAR2(4000) PATH '/IMA/FA_REPORTS/NO_FIREARMS_REPORTED_DETAILS/NO_FIREARMS_REPORTED_REASON[not(fox-error)]/text()'
    , supplementary_report_xml XMLTYPE PATH '/IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST'
    , is_complete VARCHAR2(5) PATH '/IMA/FA_REPORTS/REPORT_COMPLETED_FLAG[not(fox-error)]/text()'
    , completed_by_id NUMBER PATH
      '/IMA/FA_REPORTS/HISTORICAL_REPORT_COMPLETION_LIST/HISTORICAL_REPORT_COMPLETION[last()]/REPORT_COMPLETED_BY_WUA_ID[last()]/text()'
    , completed_datetime VARCHAR(20) PATH
      '/IMA/FA_REPORTS/HISTORICAL_REPORT_COMPLETION_LIST/HISTORICAL_REPORT_COMPLETION[last()]/REPORT_COMPLETED_DATETIME[last()]/text()'
{common_xml_fields}
  ) x
WHERE status_control = 'C'
""".format(
    common_xml_fields=common_xml_fields
)


dfl_checklist_columns = """
      , certificate_attached VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/DAF_DEACTIVATION_CERTIFICATE_ATTACHED[not(fox-error)]/text()'
      , certificate_issued VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/DAF_DEACTIVATION_CERTIFICATE_ISSUED[not(fox-error)]/text()'
"""


dfl_application = import_application_base.format(
    **{
        "subquery": dfl_application_subquery,
        "ima_type": "FA",
        "ima_sub_type": "DEACTIVATED",
        "process_type": ProcessTypes.FA_DFL,
    }
)


dfl_checklist = import_checklist_base.format(
    **{"columns": dfl_checklist_columns, "ima_type": "FA", "ima_sub_type": "DEACTIVATED"}
)
