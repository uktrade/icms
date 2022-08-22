from .export import export_application_base

__all__ = ["cfs_application"]

cfs_subquery = """
  SELECT cad.id cad_id, XMLTYPE.getClobVal(schedule_xml) schedule_xml
  FROM impmgr.certificate_app_details cad,
    XMLTABLE('/*'
    PASSING cad.xml_data
    COLUMNS schedule_xml XMLTYPE PATH '/CA/APPLICATION/PRODUCTS/SCHEDULE_LIST'
  ) x
"""

cfs_application = export_application_base.format(
    **{
        "process_type": "CertificateOfFreeSaleApplication",
        "application_details": cfs_subquery,
        "application_type": "CFS",
    }
)
