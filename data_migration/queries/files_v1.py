# TODO: ICMSLST-2116 Remove this file and use the queries found in files.py

QUERY_1 = f"""
    SELECT
    sld.blob_data
    , fv.path
    , fv.created_by_id
    , fv.created_datetime
    FROM mailshotmgr.xview_mailshot_details xmd
    INNER JOIN decmgr.file_folders ff ON ff.id = xmd.documents_ff_id
    INNER JOIN decmgr.file_folder_targets fft ON fft.ff_id = ff.id
    INNER JOIN (
    SELECT
        fft_id target_id
        , fv.id version_id
        , create_start_datetime created_datetime
        , create_by_wua_id created_by_id
        , CONCAT(id, CONCAT('-', x.filename)) PATH
        , secure_lob_ref
        , x.*
    FROM decmgr.file_versions fv
    CROSS JOIN XMLTABLE('/*'
        PASSING metadata_xml
        COLUMNS
        filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
        , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
        , file_size NUMBER PATH '/file-metadata/size/text()'
        ) x
    WHERE status_control = 'C'
    ) fv ON fv.target_id = fft.ID
    INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(fv.secure_lob_ref).id
    WHERE xmd.status_control = 'C' AND created_datetime > TO_DATE('{{created_datetime_from}}', 'YYYY/MM/DD HH24:MI:SS`')
    ORDER BY fv.created_datetime ASC, fft.id
"""  # noqa: F541

QUERY_2 = f"""
    SELECT
    sld.blob_data
    , fv.path
    , fv.created_by_id
    , fv.created_datetime
    FROM impmgr.xview_ima_rfis xir
    INNER JOIN decmgr.file_folders ff ON ff.id = xir.file_folder_id
    INNER JOIN decmgr.file_folder_targets fft ON fft.ff_id = ff.id
    INNER JOIN (
    SELECT
        fft_id target_id
        , fv.id version_id
        , create_start_datetime created_datetime
        , create_by_wua_id created_by_id
        , CONCAT(id, CONCAT('-', x.filename)) PATH
        , secure_lob_ref
        , x.*
    FROM decmgr.file_versions fv
    CROSS JOIN XMLTABLE('/*'
        PASSING metadata_xml
        COLUMNS
        filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
        , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
        , file_size NUMBER PATH '/file-metadata/size/text()'
        ) x
    WHERE status_control = 'C'
    ) fv ON fv.target_id = fft.ID
    INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(fv.secure_lob_ref).id
    WHERE created_datetime > TO_DATE('{{created_datetime_from}}', 'YYYY/MM/DD HH24:MI:SS`')
    ORDER by created_datetime ASC, fft.id
"""  # noqa: F541

QUERY_3 = f"""
    SELECT
    sld.blob_data
    , fv.path
    , fv.created_by_id
    , fv.created_datetime
    FROM decmgr.file_folder_targets fft
    INNER JOIN decmgr.file_folders ff ON fft.ff_id = ff.id
    INNER JOIN (
    SELECT
        fft_id target_id
        , fv.id version_id
        , create_start_datetime created_datetime
        , create_by_wua_id created_by_id
        , CONCAT(id, CONCAT('-', x.filename)) PATH
        , secure_lob_ref
        , x.*
    FROM decmgr.file_versions fv
    CROSS JOIN XMLTABLE('/*'
        PASSING metadata_xml
        COLUMNS
        filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
        , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
        , file_size NUMBER PATH '/file-metadata/size/text()'
        ) x
    WHERE status_control = 'C'
    ) fv ON fv.target_id = fft.ID
    INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(fv.secure_lob_ref).id
    WHERE ff.file_folder_type IN ('IMP_CASE_NOTE_DOCUMENTS', 'GMP_SUPPORTING_DOCUMENTS')
    AND created_datetime > TO_DATE('{{created_datetime_from}}', 'YYYY/MM/DD HH24:MI:SS`')
    ORDER by created_datetime ASC, fft.id
"""  # noqa: F541


QUERY_4 = f"""
    SELECT
    sld.blob_data
    , fv.path
    , fv.created_by_id
    , fv.created_datetime
    FROM impmgr.xview_ima_details xid
    INNER JOIN impmgr.import_application_types iat
    ON iat.ima_type = xid.ima_type AND iat.ima_sub_type = xid.ima_sub_type
    INNER JOIN decmgr.file_folders ff ON ff.id = xid.app_docs_ff_id
    INNER JOIN decmgr.file_folder_targets fft ON fft.ff_id = ff.id
    INNER JOIN (
    SELECT
        fft_id
        , fv.id version_id
        , create_start_datetime created_datetime
        , create_by_wua_id created_by_id
        , CONCAT(id, CONCAT('-', x.filename)) path
        , secure_lob_ref
        , x.*
    FROM decmgr.file_versions fv
    CROSS JOIN XMLTABLE('/*'
        PASSING fv.metadata_xml
        COLUMNS
        filename VARCHAR2(4000) PATH '/file-metadata/filename/text()'
        , content_type VARCHAR2(4000) PATH '/file-metadata/content-type/text()'
        , file_size NUMBER PATH '/file-metadata/size/text()'
    ) x
    WHERE status_control = 'C'
    ) fv ON fv.fft_id = fft.id
    INNER JOIN securemgr.secure_lob_data sld ON sld.id = DEREF(fv.secure_lob_ref).id
    WHERE xid.status_control = 'C' AND created_datetime > TO_DATE('{{created_datetime_from}}', 'YYYY/MM/DD HH24:MI:SS`')
    AND xid.status <> 'DELETED'
    AND (
    (iat.status = 'ARCHIVED' AND xid.submitted_datetime IS NOT NULL)
    OR iat.status = 'CURRENT'
    )
    order by created_datetime ASC, version_id asc
"""  # noqa: F541


QUERY_5 = f"""
    SELECT
    sld.blob_data
    , vf.file_id || '-' || vf.filename PATH
    , vf.created_by_wua_id created_by_id
    , vf.created_datetime
    FROM doclibmgr.folder_details fd
    INNER JOIN doclibmgr.vw_file_folders vff ON vff.f_id = fd.f_id
    INNER JOIN doclibmgr.vw_files vf ON vf.file_id = vff.file_id
    INNER JOIN DOCLIBMGR.FILE_versions fv ON fv.id = vf.file_id
    INNER JOIN securemgr.secure_lob_data sld ON sld.id = fv.secure_lob_id
    WHERE fd.folder_title LIKE 'Case Note %' AND vf.created_datetime > TO_DATE('{{created_datetime_from}}', 'YYYY/MM/DD HH24:MI:SS`')
    ORDER BY fv.created_datetime ASC, vf.file_id
"""  # noqa: F541

QUERY_6 = f"""
    SELECT
    glf.file_content as blob_data
    , CONCAT(glf.id, CONCAT('/', x.filename)) path
    , x.created_by_id
    , TO_DATE(x.created_datetime, 'YYYY-MM-DD"T"HH24:MI:SS') AS created_datetime
    FROM impmgr.import_application_details ad
    INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_type = 'FA'
    CROSS JOIN XMLTABLE('
    for $g1 in /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT | <null/>
    where /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT and not($g1/self::null)
    return
    for $g2 in $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE | <null/>
    where $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE and not($g2/self::null)
    return
    for $g3 in $g2/FILE_UPLOAD_LIST/FILE_UPLOAD | <null/>
    where $g2/FILE_UPLOAD_LIST/FILE_UPLOAD and not ($g3/self::null)
    return
    <uploads>
    <created_by_id>{{{{$g1/FA_SUPPLEMENTARY_REPORT_DETAILS/SUBMITTED_BY_WUA_ID/text()}}}}</created_by_id>
    <file_id>{{{{$g3/FILE_CONTENT/file-id/text()}}}}</file_id>
    <filename>{{{{$g3/FILE_CONTENT/filename/text()}}}}</filename>
    <created_datetime>{{{{$g3/FILE_CONTENT/upload-date-time/text()}}}}</created_datetime>
    </uploads>
    '
    PASSING ad.xml_data
    COLUMNS
    created_by_id INTEGER PATH '/uploads/created_by_id/text()'
    , created_datetime VARCHAR(4000) PATH '/uploads/created_datetime/text()'
    , sr_goods_file_id VARCHAR(4000) PATH '/uploads/file_id/text()'
    , filename VARCHAR(4000) PATH '/uploads/filename/text()'
    ) x
    INNER JOIN impmgr.goods_line_files glf ON glf.id = x.sr_goods_file_id
    WHERE ad.status_control = 'C' AND created_datetime > '{{created_datetime_from}}'
    ORDER BY created_datetime
"""  # noqa: F541


QUERY_LIST = [
    {
        "query": QUERY_1,
        "query_name": "V1_QUERY_1",
    },
    {
        "query": QUERY_2,
        "query_name": "V1_QUERY_2",
    },
    {
        "query": QUERY_3,
        "query_name": "V1_QUERY_3",
    },
    {
        "query": QUERY_4,
        "query_name": "V1_QUERY_4",
    },
    {
        "query": QUERY_5,
        "query_name": "V1_QUERY_5",
    },
    {
        "query": QUERY_6,
        "query_name": "V1_QUERY_6",
    },
]

AVAILABLE_QUERIES = [query["query_name"] for query in QUERY_LIST]
