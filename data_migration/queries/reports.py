report_files = r"""
SELECT
    rpo.id as report_output_id
    , rs.id AS schedule_id
    , to_char(rp.FINISH_DATETIME,'YYYYMMDD') || '_' || rp.PART_LABEL
    || '--' || REGEXP_REPLACE(rs.TITLE, '\s+', '_') || '.csv' AS filename
    , 'application/csv' AS content_type
    , dbms_lob.getlength(rpo.CLOB_DATA) file_size
    , 'REPORTS/LEGACY/' || rs.id  || '/' || to_char(rp.FINISH_DATETIME,'YYYYMMDD') || '_' || rp.PART_LABEL
    || '--' || REGEXP_REPLACE(rs.TITLE, '\s+', '_') || '.csv' AS path
    , rp.FINISH_DATETIME AS created_datetime
    , 0 AS created_by_id
    , rpo.CLOB_DATA
FROM REPORTMGR.REPORT_PARTS_OUTPUTS rpo
INNER JOIN REPORTMGR.REPORT_PARTS rp ON rpo.RP_ID = rp.id
INNER JOIN REPORTMGR.REPORT_RUNS rr ON rp.rr_id = rr.id
INNER JOIN REPORTMGR.REPORT_PART_STATUS rps ON rp.id = rps.RP_ID
INNER JOIN REPORTMGR.REPORT_SCHEDULES rs ON rr.RS_ID = rs.id
WHERE rp.PART_LABEL NOT IN ('PARAMETER_DATA', 'PARAMETERS')
AND	rpo.OUTPUT_TYPE ='CSV'
AND rps.RUN_STATUS = 'COMPLETE'
AND rr."DOMAIN" != 'APP_ERRORS'
AND rpo.id > :report_output_id
ORDER BY report_output_id
"""


schedule_reports = """
SELECT
    rs.id AS id
    , rr."DOMAIN" AS report_domain
    , rs.TITLE
    , rs.DESCRIPTION AS notes
    , rr.PARAMETER_XML as parameters_xml
    , rs.SCHEDULED_BY_WUA_ID AS scheduled_by_id
    , rr.START_DATETIME AS started_at
    , rr.COMPLETED_DATETIME AS finished_at
    , rr.DELETED_DATETIME AS deleted_at
    , rr.DELETED_BY_WUA_ID AS deleted_by_id
    , JSON_OBJECT(
      'application_type' IS app_type
      , 'date_from' IS start_date
      , 'date_to' IS end_date
      , 'case_submitted_date_from' IS submit_start_date
      , 'case_submitted_date_to' IS submit_end_date
      , 'case_closed_date_from' IS closed_start_date
      , 'case_closed_date_to' IS closed_end_date
      , 'request_date_from' IS request_start_date
      , 'request_date_to' IS request_end_date
      ) AS parameters
FROM reportmgr.REPORT_SCHEDULES rs
INNER JOIN REPORTMGR.REPORT_RUNS rr ON rs.id = rr.rs_id
CROSS JOIN XMLTABLE('/*'
PASSING rr.PARAMETER_XML
COLUMNS
  app_type VARCHAR2(4000) PATH '/PARAMETER_LIST/PARAMETER[NAME="APP_TYPE"]/VALUE/text()'
  , start_date VARCHAR2(10) PATH '/PARAMETER_LIST/PARAMETER[NAME="REPORT_PERIOD"]/VALUE/START_DATE/text()'
  , end_date VARCHAR2(10) PATH '/PARAMETER_LIST/PARAMETER[NAME="REPORT_PERIOD"]/VALUE/END_DATE/text()'
  , submit_start_date VARCHAR2(10) PATH '/PARAMETER_LIST/PARAMETER[NAME="SUBMIT_PERIOD"]/VALUE/START_DATE/text()'
  , submit_end_date VARCHAR2(10) PATH '/PARAMETER_LIST/PARAMETER[NAME="SUBMIT_PERIOD"]/VALUE/END_DATE/text()'
  , closed_start_date VARCHAR2(10) PATH '/PARAMETER_LIST/PARAMETER[NAME="CLOSED_PERIOD"]/VALUE/START_DATE/text()'
  , closed_end_date VARCHAR2(10) PATH '/PARAMETER_LIST/PARAMETER[NAME="CLOSED_PERIOD"]/VALUE/END_DATE/text()'
  , request_start_date VARCHAR2(10) PATH '/PARAMETER_LIST/PARAMETER[NAME="REQUEST_PERIOD"]/VALUE/START_DATE/text()'
  , request_end_date VARCHAR2(10) PATH '/PARAMETER_LIST/PARAMETER[NAME="REQUEST_PERIOD"]/VALUE/END_DATE/text()'
) x
WHERE rr."DOMAIN" != 'APP_ERRORS'
ORDER BY rs.id
"""
