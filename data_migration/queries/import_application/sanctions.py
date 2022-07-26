from web.flow.models import ProcessTypes

from .import_application import common_xml_fields, import_application_base

__all__ = ["sanctions_application"]


sanctions_application_subquery = """
SELECT
  ad.ima_id, ad.id imad_id, x.*
FROM impmgr.import_application_details ad,
  XMLTABLE('/*'
  PASSING ad.xml_data
  COLUMNS
    exporter_name VARCHAR2(4000) PATH '/IMA/APP_DETAILS/ADHOC_DETAILS/EXPORTER_NAME/text()'
    , exporter_address VARCHAR2(4000) PATH '/IMA/APP_DETAILS/ADHOC_DETAILS/EXPORTER_ADDRESS/text()'
    , commodities_xml XMLTYPE PATH '/IMA/APP_DETAILS/ADHOC_DETAILS/COMMODITY_LIST'
    , sanction_emails_xml XMLTYPE PATH '/IMA/APP_PROCESSING/SANCTION_EMAIL_MASTER/SANCTION_EMAIL_LIST'
{common_xml_fields}
  ) x
WHERE status_control = 'C'
""".format(
    common_xml_fields=common_xml_fields
)


sanctions_application = import_application_base.format(
    **{
        "subquery": sanctions_application_subquery,
        "ima_type": "ADHOC",
        "ima_sub_type": "ADHOC1",
        "process_type": ProcessTypes.SANCTIONS,
    }
)
