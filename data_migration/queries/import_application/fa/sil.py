from data_migration.queries.import_application.import_application import (
    import_application_base,
    import_checklist_base,
)
from web.flow.models import ProcessTypes

sil_application_subquery = """
SELECT
  ad.ima_id
  , ad.id imad_id
  , CASE x.section1 WHEN 'SEC1' THEN 1 ELSE 0 END section1
  , CASE x.section2 WHEN 'SEC2' THEN 1 ELSE 0 END section2
  , CASE x.section5 WHEN 'SEC5' THEN 1 ELSE 0 END section5
  , CASE x.section58_obsolete WHEN 'SEC5_OBSOLETE' THEN 1 ELSE 0 END section58_obsolete
  , CASE x.section58_other WHEN 'SECTION_OTHER' THEN 1 ELSE 0 END section58_other
  , x.other_description
  , CASE x.military_police WHEN 'Y' THEN 1 WHEN 'N' THEN 0 ELSE NULL END military_police
  , CASE x.eu_single_market WHEN 'Y' THEN 1 WHEN 'N' THEN 0 ELSE NULL END eu_single_market
  , CASE x.manufactured WHEN 'Y' THEN 1 WHEN 'N' THEN 0 ELSE NULL END manufactured
  , x.commodity_code commodity_group_id
  , CASE x.know_bought_from WHEN 'Y' THEN 1 WHEN 'N' THEN 0 ELSE NULL END know_bought_from
  , x.additional_comments
  , x.cover_letter
  , x.fa_authorities_xml
  , x.section5_authorities_xml
  , x.bought_from_details_xml
  , XMLTYPE.getClobVal(x.supplementary_report_xml) supplementary_report_xml
  , CASE x.is_complete WHEN 'true' THEN 1 ELSE 0 END is_complete
  , x.no_report_reason
  , CASE WHEN x.completed_by_id IS NOT NULL THEN 2 ELSE NULL END completed_by_id
  , TO_DATE(x.completed_datetime, 'YYYY-MM-DD') completed_datetime
  , XMLTYPE.getClobVal(commodities_xml) commodities_xml
  , XMLTYPE.getClobVal(user_import_certs_xml) user_import_certs_xml
  , x.file_folder_id
FROM impmgr.import_application_details ad,
  XMLTABLE('/*'
  PASSING ad.xml_data
  COLUMNS
    section1 VARCHAR2(4) PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION_LIST/SECTION[text()="SEC1"]/text()'
    , section2 VARCHAR2(4) PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION_LIST/SECTION[text()="SEC2"]/text()'
    , section5 VARCHAR2(4) PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION_LIST/SECTION[text()="SEC5"]/text()'
    , section58_obsolete VARCHAR2(13) PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION_LIST/SECTION[text()="SEC5_OBSOLETE"]/text()'
    , section58_other VARCHAR2(10) PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION_LIST/SECTION[text()="SEC5_OTHER"]/text()'
    , other_description VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION_OTHER[not(fox-error)]/text()'
    , military_police VARCHAR2(10) PATH '/IMA/APP_DETAILS/FA_DETAILS/MILITARY_OR_POLICE[not(fox-error)]/text()'
    , eu_single_market VARCHAR2(10) PATH '/IMA/APP_DETAILS/FA_DETAILS/SINGLE_MARKET_BEFORE_SEP2018[not(fox-error)]/text()'
    , manufactured VARCHAR2(10) PATH '/IMA/APP_DETAILS/FA_DETAILS/ANY_MANUFACTURED_BEFORE_1939[not(fox-error)]/text()'
    , commodity_code VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/COMMODITY_GROUP[not(fox-error)]/text()'
    , know_bought_from VARCHAR2(10) PATH '/IMA/APP_DETAILS/SH_DETAILS/IS_SELLER_HOLDER_PROVIDED[not(fox-error)]/text()'
    , additional_comments VARCHAR2(4000) PATH '/IMA/APP_DETAILS/FA_DETAILS/ADDITIONAL_INFORMATION[not(fox-error)]/text()'
    , commodities_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/COMMODITY_LIST'
    , user_import_certs_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/FIREARMS_CERTIFICATE_LIST'
    , fa_authorities_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/FIREARMS_AUTHORITIES/AUTHORITY_LIST'
    , section5_authorities_xml XMLTYPE PATH '/IMA/APP_DETAILS/FA_DETAILS/SECTION5_AUTHORITIES/AUTHORITY_LIST'
    , bought_from_details_xml XMLTYPE PATH 'IMA/APP_DETAILS/FA_DETAILS/SH_DETAILS/SELLER_HOLDER_LIST'
    , no_report_reason VARCHAR2(4000) PATH '/IMA/FA_REPORTS/NO_FIREARMS_REPORTED_DETAILS/NO_FIREARMS_REPORTED_REASON[not(fox-error)]/text()'
    , supplementary_report_xml XMLTYPE PATH '/IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST'
    , cover_letter VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/RESPONSE/APPROVE/COVER_LETTER/text()'
    , is_complete VARCHAR2(5) PATH '/IMA/FA_REPORTS/REPORT_COMPLETED_FLAG[not(fox-error)]/text()'
    , completed_by_id NUMBER PATH
      '/IMA/FA_REPORTS/HISTORICAL_REPORT_COMPLETION_LIST/HISTORICAL_REPORT_COMPLETION[last()]/REPORT_COMPLETED_BY_WUA_ID[last()]/text()'
    , completed_datetime VARCHAR(20) PATH
      '/IMA/FA_REPORTS/HISTORICAL_REPORT_COMPLETION_LIST/HISTORICAL_REPORT_COMPLETION[last()]/REPORT_COMPLETED_DATETIME[last()]/text()'
    , file_folder_id INTEGER PATH '/IMA/APP_METADATA/APP_DOCS_FF_ID/text()'
  ) x
  WHERE status_control = 'C'
"""

sil_checklist_columns = """
      , authority_required VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/FA_AUTHORITY_TO_POSSESS_REQ[not(fox-error)]/text()'
      , authority_received VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/FA_AUTHORITY_TO_POSSESS_REC[not(fox-error)]/text()'
      , auth_cover_items_listed VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/FA_AUTHORITY_TO_POSSESS_COVERS_LISTED[not(fox-error)]/text()'
      , within_auth_restrictions VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/FA_WITHIN_AUTHORITY[not(fox-error)]/text()'
      , authority_police VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/FA_AUTHORITY_TO_POSSESS_CHECK[not(fox-error)]/text()'
      , update_required VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_UPDATE_REQUIRED[not(fox-error)]/text()'
      , fir_required VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_FIR_REQUIRED[not(fox-error)]/text()'
      , response_preparation VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_DECISION_RESPONSE[not(fox-error)]/text()'
      , validity_period_correct VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_VALIDITY_PERIOD[not(fox-error)]/text()'
      , endorsements_listed VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_ENDORSEMENTS[not(fox-error)]/text()'
      , authorisation VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/GEN_AUTHORISATION[not(fox-error)]/text()'
"""


sil_application = import_application_base.format(
    **{
        "subquery": sil_application_subquery,
        "ima_type": "FA",
        "ima_sub_type": "SIL",
        "process_type": ProcessTypes.FA_SIL,
    }
)

sil_checklist = import_checklist_base.format(
    **{"columns": sil_checklist_columns, "ima_type": "FA", "ima_sub_type": "SIL"}
)
