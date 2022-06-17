from web.flow.models import ProcessTypes

from .import_application import import_application_base, import_checklist_base

__all__ = ["opt_application", "opt_checklist"]


opt_application_subquery = """
  SELECT
    ad.ima_id, ad.id imad_id, x.*
  FROM impmgr.import_application_details ad,
    XMLTABLE('/*'
    PASSING ad.xml_data
    COLUMNS
      customs_office_name VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/CUSTOMS_OFFICE_NAME[not(contains(text(), "<script>alert"))]/text()'
      , customs_office_address VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/CUSTOMS_OFFICE_ADDRESS[not(contains(text(), "<script>alert"))]/text()'
      , rate_of_yield VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/RATE_OF_YIELD[not(contains(text(), "<script>alert"))]/text()'
      , rate_of_yield_calc_method VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/METHOD_OF_CALCULATION[not(contains(text(), "<script>alert"))]/text()'
      , last_export_day VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/LAST_DAY_OF_EXPORTATION[not(contains(text(), "<script>alert"))]/text()'
      , reimport_period VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/PERIOD_FOR_REIMPORTATION[not(contains(text(), "<script>alert"))]/text()'
      , nature_process_ops VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/NATURE_OF_PROCESSING[not(contains(text(), "<script>alert"))]/text()'
      , suggested_id VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/MEANS_OF_IDENTIFICATION[not(contains(text(), "<script>alert"))]/text()'
      , cp_origin_country_id VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/COMPENSATING_PRODUCTS/COUNTRY_OF_ORIGIN/text()'
      , cp_processing_country_id VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/COMPENSATING_PRODUCTS/COUNTRY_OF_PROCESSING/text()'
      , commodity_group_id VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/COMPENSATING_PRODUCTS/COMMODITY_GROUP/text()'
      , cp_total_quantity VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/COMPENSATING_PRODUCTS/QUANTITY/text()'
      , cp_total_value VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/COMPENSATING_PRODUCTS/VALUE[not(contains(text(), "<script>alert"))]/text()'
      , cp_commodities_xml XMLTYPE PATH '/IMA/APP_DETAILS/OPT_DETAILS/COMPENSATING_PRODUCTS/COMMODITY_LIST'
      , teg_origin_country_id VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/TEMPORARY_GOODS/COUNTRY_OF_ORIGIN/text()'
      , teg_total_quantity VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/TEMPORARY_GOODS/QUANTITY/text()'
      , teg_total_value VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/TEMPORARY_GOODS/VALUE[not(contains(text(), "<script>alert"))]/text()'
      , teg_goods_description VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/TEMPORARY_GOODS/COMMODITY_DESC[not(contains(text(), "<script>alert"))]/text()'
      , teg_commodities_xml XMLTYPE PATH '/IMA/APP_DETAILS/OPT_DETAILS/TEMPORARY_GOODS/COMMODITY_LIST'
      , fq_similar_to_own_factory VARCHAR2(5) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/MANUFACTURE_SIMILAR_GOODS/text()'
      , fq_manufacturing_within_eu VARCHAR2(5) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/MAIN_MANUFACTURING_PROCESSES/text()'
      , fq_maintained_in_eu VARCHAR2(5) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/MAINTAINED_TEXTILE_ACTIVITY/text()'
      , fq_maintained_in_eu_reasons VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/MAINTAINED_TEXTILE_ACTIVITY_EXPLANATION/text()'
      , fq_employment_decreased VARCHAR2(5) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/LEVEL_OF_EMPLOYMENT_DECREASED/text()'
      , fq_employment_decreased_r VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/LEVEL_OF_EMPLOYMENT_DECREASED_EXPLANATION/text()'
      , fq_prior_authorisation VARCHAR2(5) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/PRIOR_AUTHORISATION/text()'
      , fq_prior_auth_reasons VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/PRIOR_AUTHORISATION_EXPLANATION/text()'
      , fq_past_beneficiary VARCHAR2(5) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/PAST_BENEFICIARY/text()'
      , fq_past_beneficiary_r VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/PAST_BENEFICIARY_EXPLANATION/text()'
      , fq_new_application VARCHAR2(5) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/NEW_APPLICATION/text()'
      , fq_new_application_reasons VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/NEW_APPLICATION_EXPLANATION/text()'
      , fq_further_authorisation VARCHAR2(5) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/FURTHER_AUTHORISATION/text()'
      , fq_further_auth_reasons VARCHAR2(4000) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/FURTHER_AUTHORISATION_EXPLANATION/text()'
      , fq_subcontract_production VARCHAR2(5) PATH '/IMA/APP_DETAILS/OPT_DETAILS/OPT_QUESTIONS/SUBCONTRACT_PRODUCTION/text()'
      , cover_letter VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/RESPONSE/APPROVE/COVER_LETTER/text()'
      , file_folder_id INTEGER PATH '/IMA/APP_METADATA/APP_DOCS_FF_ID/text()'
    ) x
    WHERE status_control = 'C'
"""

opt_checklist_columns = """
      , operator_requests_submitted VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/OPT_OPERATOR_REQUESTS/text()'
      , authority_to_issue VARCHAR2(4000) PATH '/IMA/APP_PROCESSING/CHECKLIST/OPT_AUTHORITY_TO_ISSUE_CONFIRMED/text()'
"""

opt_application = import_application_base.format(
    **{
        "subquery": opt_application_subquery,
        "ima_type": "OPT",
        "ima_sub_type": "QUOTA",
        "process_type": ProcessTypes.OPT,
    }
)

opt_checklist = import_checklist_base.format(
    **{"columns": opt_checklist_columns, "ima_type": "OPT", "ima_sub_type": "QUOTA"}
)
