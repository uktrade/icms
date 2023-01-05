from web.flow.models import ProcessTypes

from ..base import common_xml_fields, import_application_base, import_checklist_base

oil_application_subquery = """
SELECT
  ad.ima_id
  , ad.id imad_id
  , CASE x.section1 WHEN 'SEC1' THEN 1 ELSE 0 END section1
  , CASE x.section2 WHEN 'SEC2' THEN 1 ELSE 0 END section2
  , x.commodity_code commodity_group_id
  , CASE x.know_bought_from WHEN 'Y' THEN 1 WHEN 'N' THEN 0 ELSE NULL END know_bought_from
  , x.additional_comments
  , XMLTYPE.getClobVal(x.cover_letter) cover_letter
  , x.commodities_xml
  , x.user_import_certs_xml
  , x.fa_authorities_xml
  , XMLTYPE.getClobVal(x.bought_from_details_xml) bought_from_details_xml
  , XMLTYPE.getClobVal(x.supplementary_report_xml) supplementary_report_xml
  , CASE x.is_complete WHEN 'true' THEN 1 ELSE 0 END is_complete
  , x.no_report_reason
  , x.completed_by_id
  , TO_DATE(x.completed_datetime, 'YYYY-MM-DD') completed_datetime
  , x.file_folder_id
FROM impmgr.import_application_details ad
CROSS JOIN XMLTABLE('/*'
  PASSING ad.xml_data
  COLUMNS
    section1 VARCHAR2(4) PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION_LIST/SECTION[text()="SEC1"]/text()'
    , section2 VARCHAR2(4) PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION_LIST/SECTION[text()="SEC2"]/text()'
    , commodity_code VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/COMMODITY_GROUP[not(fox-error)]/text()'
    , know_bought_from VARCHAR2(10) PATH '/IMA/APP_DETAILS/SH_DETAILS/IS_SELLER_HOLDER_PROVIDED[not(fox-error)]/text()'
    , additional_comments VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/ADDITIONAL_INFORMATION[not(fox-error)]/text()'
    , commodities_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/COMMODITY_LIST'
    , user_import_certs_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/FIREARMS_CERTIFICATE_LIST'
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


oil_checklist_columns = """
  , authority_required VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/FA_AUTHORITY_TO_POSSESS_REQ[not(fox-error)]/text()'
  , authority_received VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/FA_AUTHORITY_TO_POSSESS_REC[not(fox-error)]/text()'
  , authority_police VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/FA_AUTHORITY_TO_POSSESS_CHECK[not(fox-error)]/text()'
"""


oil_application = import_application_base.format(
    **{
        "subquery": oil_application_subquery,
        "ima_type": "FA",
        "ima_sub_type": "OIL",
        "process_type": ProcessTypes.FA_OIL,
    }
)


oil_checklist = import_checklist_base.format(
    **{"columns": oil_checklist_columns, "ima_type": "FA", "ima_sub_type": "OIL"}
)
