__all__ = ["import_application_licence"]

# TODO ICMSLST-1494: Expand to cover all application types
# TODO ICMSLST-1494: Find how to determine if paper only

import_application_licence = """
SELECT
  imad_id
  , created_datetime
  , CASE licence_validity WHEN 'CURRENT' THEN 'AC' ELSE 'AR' END status
  , licence_start_date
  , licence_end_date
FROM impmgr.ima_responses ir
INNER JOIN impmgr.ima_response_details ird ON ird.ir_id = ir.id
INNER JOIN impmgr.import_application_details iad ON iad.id = ird.imad_id
WHERE response_type = 'TEX_QUOTA_LICENCE'
AND iad.status_control = 'C'
"""
