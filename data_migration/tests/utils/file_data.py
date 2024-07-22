import datetime as dt

from data_migration import queries

FOLDER_COLUMNS = [
    ("folder_id",),
    ("folder_type",),
]

APPLICATION_FOLDER_COLUMNS = FOLDER_COLUMNS + [("app_model",)]

TARGET_COLUMNS = [
    ("folder_id",),
    ("target_type",),
    ("status",),
    ("target_id",),
]

FILES_COLUMNS = [
    ("target_id",),
    ("version_id",),
    ("created_datetime",),
    ("created_by_id",),
    ("path",),
    ("filename",),
    ("content_type",),
    ("file_size",),
]

file_query_result = {
    #
    # Import Application
    #
    queries.import_application_folders: (
        APPLICATION_FOLDER_COLUMNS,
        [
            (
                100,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "priorsurveillanceapplication",  # app_model
            ),
            (
                101,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "priorsurveillanceapplication",  # app_model
            ),
            (
                41,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "textilequotaapplication",  # app_model
            ),
            (
                42,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "textilequotaapplication",  # app_model
            ),
            (
                43,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "textilequotaapplication",  # app_model
            ),
            (
                51,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "dflapplication",  # app_model
            ),
            (
                52,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "dflapplication",  # app_model
            ),
            (
                53,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "dflapplication",  # app_model
            ),
            (
                60,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "sanctionsapplication",  # app_model
            ),
            (
                21,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "openindividuallicenceapplication",  # app_model
            ),
            (
                22,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "openindividuallicenceapplication",  # app_model
            ),
            (
                23,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "openindividuallicenceapplication",  # app_model
            ),
            (
                1,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "silapplication",  # app_model
            ),
            (
                2,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "silapplication",  # app_model
            ),
            (
                3,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "silapplication",  # app_model
            ),
            (
                10,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "outwardprocessingtradeapplication",  # app_model
            ),
            (
                11,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "outwardprocessingtradeapplication",  # app_model
            ),
        ],
    ),
    queries.import_application_file_targets: (
        TARGET_COLUMNS,
        [
            # SPS Application
            (
                100,  # folder_id
                "IMP_SPS_DOC",  # target_type
                "RECEIVED",  # status
                1000,  # target_id
            ),
            (
                101,  # folder_id
                "IMP_SPS_DOC",  # target_type
                "RECEIVED",  # status
                1001,  # target_id
            ),
            (
                100,  # folder_id
                "IMP_SUPPORTING_DOC",  # target_type
                "RECEIVED",  # status
                1002,  # target_id
            ),
            (
                100,  # folder_id
                "IMP_SUPPORTING_DOC",  # target_type
                "RECEIVED",  # status
                1003,  # target_id
            ),
            (
                101,  # folder_id
                "IMP_SUPPORTING_DOC",  # target_type
                "RECEIVED",  # status
                1004,  # target_id
            ),
            # Textiles Application
            (
                41,  # folder_id
                "IMP_APP_DOCUMENTS",  # target_type
                "EMPTY",  # status
                5100,  # target_id
            ),
            (
                42,  # folder_id
                "IMP_APP_DOCUMENTS",  # target_type
                "EMPTY",  # status
                5101,  # target_id
            ),
            (
                43,  # folder_id
                "IMP_APP_DOCUMENTS",  # target_type
                "EMPTY",  # status
                5103,  # target_id
            ),
            # DFL Application
            (
                51,  # folder_id
                "IMP_SUPPORTING_DOCS",  # target_type
                "RECEIVED",  # status
                5000,  # target_id
            ),
            (
                51,  # folder_id
                "IMP_SUPPORTING_DOCS",  # target_type
                "RECEIVED",  # status
                5001,  # target_id
            ),
            (
                52,  # folder_id
                "IMP_SUPPORTING_DOCS",  # target_type
                "EMPTY",  # status
                5002,  # target_id
            ),
            # Sanctions Application
            (
                60,  # folder_id
                "IMP_SUPPORTING_DOCS",  # target_type
                "EMPTY",  # status
                6000,  # target_id
            ),
            # OIL Application
            (
                21,  # folder_id
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                3000,  # target_id
            ),
            (
                22,  # folder_id
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                3001,  # target_id
            ),
            (
                23,  # folder_id
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                3002,  # target_id
            ),
            # SIL Application
            (
                1,  # folder_id
                "IMP_SECTION5_AUTHORITY",  # target_type
                "RECEIVED",  # status
                1100,  # target_id
            ),
            (
                1,  # folder_id
                "IMP_SECTION5_AUTHORITY",  # target_type
                "RECEIVED",  # status
                1101,  # target_id
            ),
            (
                2,  # folder_id
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                1103,  # target_id
            ),
            (
                3,  # folder_id
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                1104,  # target_id
            ),
            # OPT Application
            (
                10,  # folder_id
                "IMP_SUPPORTING_DOC",  # target_type
                "RECEIVED",  # status
                2000,  # target_id
            ),
            (
                11,  # folder_id
                "IMP_SUPPORTING_DOC",  # target_type
                "RECEIVED",  # status
                2001,  # target_id
            ),
        ],
    ),
    queries.import_application_files: (
        FILES_COLUMNS,
        [
            # SPS Application Files
            (
                1000,  # target_id
                10000,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "contract/file/10000",  # path
                "contract-no-content.pdf",  # filename
                None,  # content_type
                12345,  # file_size
            ),
            (
                1001,  # target_id
                10001,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "contract/file/10001",  # path
                "contract-2.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                1002,  # target_id
                10002,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "contract/file/10003",  # path
                "contract.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                1003,  # target_id
                10003,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "contract/file/10002",  # path
                "contract.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                1004,  # target_id
                10004,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "contract/file/10004",  # path
                "contract.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            # DFL Application Files
            (
                5000,  # target_id
                50000,  # version_id
                dt.datetime.now(),  # created_datetime
                2,  # created_by_id
                "goods/test_a.pdf",  # path
                "test_a.pdf",  # filename
                "pdf",  # content_type
                1000,  # file_size
            ),
            (
                5001,  # target_id
                50001,  # version_id
                dt.datetime.now(),  # created_datetime
                2,  # created_by_id
                "goods/test_b.pdf",  # path
                "test_b.pdf",  # filename
                "pdf",  # content_type
                1000,  # file_size
            ),
            # SIL Application Files
            (
                1100,  # target_id
                11000,  # version_id
                dt.datetime(2022, 4, 27, 12, 30),  # created_datetime
                2,  # created_by_id
                "contract/file/sil/10000",  # path
                "Test User Sec 5.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                1101,  # target_id
                11001,  # version_id
                dt.datetime(2022, 3, 23, 11, 47),  # created_datetime
                2,  # created_by_id
                "contract/file/sil/100001",  # path
                "Test User Sec 5 2.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            # OPT Application Files
            (
                2000,  # target_id
                20000,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "contract/file/20000",  # path
                "Test OPT supporting doc.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                2001,  # target_id
                20001,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "contract/file/20001",  # path
                "Test OPT supporting doc 2.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
        ],
    ),
    queries.fa_certificate_folders: (
        FOLDER_COLUMNS,
        [
            (
                102,  # folder_id
                "IMP_FIREARMS_AUTHORITY_DOCS",  # folder_type
            ),
            (
                103,  # folder_id
                "IMP_FIREARMS_AUTHORITY_DOCS",  # folder_type
            ),
            (
                104,  # folder_id
                "IMP_SECTION5_AUTHORITY_DOCS",  # folder_type
            ),
            (
                105,  # folder_id
                "IMP_SECTION5_AUTHORITY_DOCS",  # folder_type
            ),
            (
                106,  # folder_id
                "IMP_FIREARMS_AUTHORITY_DOCS",  # folder_type
            ),
            (
                107,  # folder_id
                "IMP_SECTION5_AUTHORITY_DOCS",  # folder_type
            ),
        ],
    ),
    queries.fa_certificate_file_targets: (
        TARGET_COLUMNS,
        [
            (
                102,  # folder_id
                "IMP_FIREARMS_AUTHORITY",  # target_type
                "RECEIVED",  # status
                1005,  # target_id
            ),
            (
                103,  # folder_id
                "IMP_FIREARMS_AUTHORITY",  # target_type
                "RECEIVED",  # status
                1006,  # target_id
            ),
            (
                103,  # folder_id
                "IMP_FIREARMS_AUTHORITY",  # target_type
                "RECEIVED",  # status
                1007,  # target_id
            ),
            (
                104,  # folder_id
                "IMP_SECTION5_AUTHORITY",  # target_type
                "RECEIVED",  # status
                1008,  # target_id
            ),
            (
                105,  # folder_id
                "IMP_SECTION5_AUTHORITY",  # target_type
                "RECEIVED",  # status
                1009,  # target_id
            ),
            (
                106,  # folder_id
                "IMP_FIREARMS_AUTHORITY",  # target_type
                "EMPTY",  # status
                1010,  # target_id
            ),
            (
                107,  # folder_id
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                1011,  # target_id
            ),
        ],
    ),
    queries.fa_certificate_files: (
        FILES_COLUMNS,
        [
            (
                1005,  # target_id
                10005,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "fa-auth/file/10005",  # path
                "fa-auth.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                1006,  # target_id
                10006,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "fa-auth/file/10006",  # path
                "fa-auth.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                1007,  # target_id
                10007,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "fa-auth/file/10007",  # path
                "fa-auth.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                1008,  # target_id
                10008,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "section5-auth/file/10008",  # path
                "section5-auth.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                1009,  # target_id
                10009,  # version_id
                dt.datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "section5-auth/file/10009",  # path
                "section5-auth.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
        ],
    ),
    queries.file_folders_folder_type: (
        FOLDER_COLUMNS,
        [
            (
                221,  # folder_id
                "IMP_CASE_NOTE_DOCUMENTS",  # folder_type
            ),
            (
                222,  # folder_id
                "IMP_CASE_NOTE_DOCUMENTS",  # folder_type
            ),
            (
                223,  # folder_id
                "IMP_CASE_NOTE_DOCUMENTS",  # folder_type
            ),
            (
                231,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
            ),
            (
                232,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
            ),
            (
                233,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
            ),
            (
                234,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
            ),
        ],
    ),
    queries.file_targets_folder_type: (
        TARGET_COLUMNS,
        [
            (
                221,  # folder_id
                "CASE_NOTE_DOCUMENT",  # target_type
                "RECEIVED",  # status
                2100,  # target_id
            ),
            (
                221,  # folder_id
                "CASE_NOTE_DOCUMENT",  # target_type
                "RECEIVED",  # status
                2101,  # target_id
            ),
            (
                222,  # folder_id
                "CASE_NOTE_DOCUMENT",  # target_type
                "RECEIVED",  # status
                2103,  # target_id
            ),
            (
                223,  # folder_id
                "CASE_NOTE_DOCUMENT",  # target_type
                "EMPTY",  # status
                2104,  # target_id
            ),
            (
                231,  # folder_id
                "ISO17021",  # target_type
                "EMPTY",  # status
                4000,  # target_id
            ),
            (
                232,  # folder_id
                "ISO17065",  # target_type
                "RECEIVED",  # status
                4001,  # target_id
            ),
            (
                232,  # folder_id
                "ISO22716",  # target_type
                "RECEIVED",  # status
                4002,  # target_id
            ),
            (
                232,  # folder_id
                "ISO17021",  # target_type
                "EMPTY",  # status
                4003,  # target_id
            ),
            (
                233,  # folder_id
                "ISO17021",  # target_type
                "RECEIVED",  # status
                4004,  # target_id
            ),
            (
                231,  # folder_id
                "BRCGS",  # target_type
                "RECEIVED",  # status
                4005,  # target_id
            ),
        ],
    ),
    queries.file_objects_folder_type: (
        FILES_COLUMNS,
        [
            # Import Application Case Notes
            (
                2100,  # target_id
                20000,  # version_id
                dt.datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "case_note/file1",  # path
                "Test Case Note 1.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                2101,  # target_id
                20001,  # version_id
                dt.datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "case_note/file2",  # path
                "Test Case Note 2.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                2103,  # target_id
                20003,  # version_id
                dt.datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "case_note/file3",  # path
                "Test Case Note 3.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            # GMP Application
            (
                4001,  # target_id
                40001,  # version_id
                dt.datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp2/ISO17065",  # path
                "ISO17065.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                4002,  # target_id
                40002,  # version_id
                dt.datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp2/ISO22716",  # path
                "ISO22716.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                4004,  # target_id
                40004,  # version_id
                dt.datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp3/ISO17021",  # path
                "ISO17021.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                4005,  # target_id
                40005,  # version_id
                dt.datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp1/BRCGS",  # path
                "BRCGS.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
        ],
    ),
    queries.fir_file_folders: (
        FOLDER_COLUMNS,
        [
            (
                200,  # folder_id
                "IMP_RFI_DOCUMENTS",  # folder_type
            ),
            (
                201,  # folder_id
                "IMP_RFI_DOCUMENTS",  # folder_type
            ),
            (
                202,  # folder_id
                "IMP_RFI_DOCUMENTS",  # folder_type
            ),
        ],
    ),
    queries.fir_file_targets: (
        TARGET_COLUMNS,
        [
            (
                200,  # folder_id
                "RFI_DOCUMENT",  # target_type
                "RECEIVED",  # status
                3100,  # target_id
            ),
            (
                200,  # folder_id
                "RFI_DOCUMENT",  # target_type
                "RECEIVED",  # status
                3101,  # target_id
            ),
            (
                201,  # folder_id
                "RFI_DOCUMENT",  # target_type
                "RECEIVED",  # status
                3103,  # target_id
            ),
            (
                202,  # folder_id
                "RFI_DOCUMENT",  # target_type
                "EMPTY",  # status
                3104,  # target_id
            ),
        ],
    ),
    queries.fir_files: (
        FILES_COLUMNS,
        [
            (
                3100,  # target_id
                30000,  # version_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "fir/file1",  # path
                "Test FIR 1.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                3101,  # target_id
                30001,  # version_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "fir/file2",  # path
                "Test FIR 2.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                3103,  # target_id
                30003,  # version_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "fir/file3",  # path
                "Test FIR 3.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
        ],
    ),
    queries.fa_supplementary_report_upload_files: (
        [
            ("created_by_id",),
            ("sr_goods_file_id",),
            ("filename",),
            ("content_type",),
            ("created_datetime",),
            ("path",),
            ("file_size",),
        ],
        [
            (
                2,  # created_by_id
                "abcde",  # sr_goods_file_id
                "SR Upload.pdf",  # filename
                "pdf",  # content_type
                "2022-11-05T12:11:03",  # created_datetime
                "abcde/SR Upload.pdf",  # path
                1234,  # file_size
            )
        ],
    ),
    #
    # Export Application
    #
    queries.export_case_note_folders: (
        [
            ("doc_folder_id",),
            ("folder_title",),
        ],
        [
            (
                1,  # doc_folder_id
                "Case Note 1",  # folder_title
            ),
            (
                2,  # doc_folder_id
                "Case Note 1",  # folder_title
            ),
            (
                3,  # doc_folder_id
                "Case Note 2",  # folder_title
            ),
            (
                4,  # doc_folder_id
                "Case Note 2",  # folder_title
            ),
        ],
    ),
    queries.export_case_note_docs: (
        [
            ("doc_folder_id",),
            ("version_id",),
            ("created_datetime",),
            ("created_by_id",),
            ("path",),
            ("filename",),
            ("content_type",),
            ("file_size",),
        ],
        [
            (
                1,  # doc_folder_id
                1,  # version_id
                dt.datetime.now(),  # created_datetime
                2,  # created_by_id
                "1-Case Note File.pdf",  # path
                "Case Note File.pdf",  # filename
                "pdf",  # content_type
                1000,  # file_size
            ),
            (
                3,  # doc_folder_id
                2,  # version_id
                dt.datetime.now(),  # created_datetime
                2,  # created_by_id
                "2-Case Note File.pdf",  # path
                "Case Note 2 File 1.pdf",  # filename
                "pdf",  # content_type
                1000,  # file_size
            ),
            (
                3,  # doc_folder_id
                3,  # version_id
                dt.datetime.now(),  # created_datetime
                2,  # created_by_id
                "3-Case Note File.pdf",  # path
                "Case Note 2 File 2.pdf",  # filename
                "pdf",  # content_type
                1000,  # file_size
            ),
        ],
    ),
    queries.mailshot_file_folders: (
        FOLDER_COLUMNS,
        [
            (2000, "MAILSHOT_DOCUMENTS"),
            (2001, "MAILSHOT_DOCUMENTS"),
            (2002, "MAILSHOT_DOCUMENTS"),
            (2003, "MAILSHOT_DOCUMENTS"),
        ],
    ),
    queries.mailshot_file_targets: (
        TARGET_COLUMNS,
        [
            (
                2000,  # folder_id
                "MAILSHOT_DOCUMENT",  # target_type
                "RECEIVED",  # status
                20000,  # target_id
            ),
            (
                2000,  # folder_id
                "MAILSHOT_DOCUMENT",  # target_type
                "RECEIVED",  # status
                20001,  # target_id
            ),
            (
                2000,  # folder_id
                "MAILSHOT_DOCUMENT",  # target_type
                "RECEIVED",  # status
                20002,  # target_id
            ),
            (
                2001,  # folder_id
                "MAILSHOT_DOCUMENT",  # target_type
                "EMPTY",  # status
                20003,  # target_id
            ),
            (
                2002,  # folder_id
                "MAILSHOT_DOCUMENT",  # target_type
                "DELETED",  # status
                20004,  # target_id
            ),
            (
                2003,  # folder_id
                "MAILSHOT_DOCUMENT",  # target_type
                "RECEIVED",  # status
                20005,  # target_id
            ),
        ],
    ),
    queries.mailshot_files: (
        FILES_COLUMNS,
        [
            (
                20000,  # target_id
                21000,  # version_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "mailshot/file1",  # path
                "Test Mailshot 1.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                20001,  # target_id
                21001,  # version_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "mailshot/file2",  # path
                "Test Mailshot 2.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                20002,  # target_id
                21002,  # version_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "mailshot/file3",  # path
                "Test Mailshot 3.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
            (
                20005,  # target_id
                21005,  # version_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "mailshot/file4",  # path
                "Test Mailshot 4.pdf",  # filename
                "pdf",  # content_type
                12345,  # file_size
            ),
        ],
    ),
    queries.report_files: (
        [
            ("report_output_id",),
            ("schedule_id",),
            ("filename",),
            ("content_type",),
            ("file_size",),
            ("path",),
            ("created_datetime",),
            ("created_by_id",),
            ("clob_data",),
        ],
        [
            (
                500,  # report_output_id
                1001,  # schedule_id
                "200204271223_ISSUED_CERTS.csv",  # filename
                "text/csv",  # content_type
                12345,  # file_size
                "REPORTS/LEGACY/200204271223_ISSUED_CERTS.csv",  # path
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "DATA",  # clob_data
            ),
            (
                501,  # report_output_id
                1002,  # schedule_id
                "200204271223_ISSUED_LICENCES.csv",  # filename
                "text/csv",  # content_type
                22223332,  # file_size
                "REPORTS/LEGACY/200204271223_ISSUED_LICENCES.csv",  # path
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                3,  # created_by_id
                "DATA",  # clob_data
            ),
            (
                502,  # report_output_id
                1003,  # schedule_id
                "200204271223_ACCESS_REQUESTS.csv",  # filename
                "text/csv",  # content_type
                12345,  # file_size
                "REPORTS/LEGACY/200204271223_ACCESS_REQUESTS.csv",  # path
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "DATA",  # clob_data
            ),
            (
                503,  # report_output_id
                1004,  # schedule_id
                "200204271223_NCA_REPORT.csv",  # filename
                "text/csv",  # content_type
                12345,  # file_size
                "REPORTS/LEGACY/200204271223_NCA_REPORT.csv",  # path
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "DATA",  # clob_data
            ),
            (
                504,  # report_output_id
                1005,  # schedule_id
                "200204271223_FIREARMS.csv",  # filename
                "text/csv",  # content_type
                12345,  # file_size
                "REPORTS/LEGACY/200204271223_FIREARMS.csv",  # path
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "DATA",  # clob_data
            ),
        ],
    ),
    queries.schedule_reports: (
        [
            ("id",),
            ("report_domain",),
            ("title",),
            ("notes",),
            ("parameter_xml",),
            ("scheduled_by_id",),
            ("created_datetime",),
            ("started_at",),
            ("finished_at",),
            ("deleted_at",),
            ("deleted_by_id",),
            ("parameters",),
        ],
        [
            (
                1001,  # id
                "IMP_ISSUED_CERTIFICATES",  # report_domain
                "Issued certs report",  # title
                "first report test",  # notes
                "",  # parameter_xml
                2,  # scheduled_by_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                dt.datetime(2022, 4, 27, 12, 23),  # started_at
                dt.datetime(2022, 4, 27, 12, 25),  # finished_at
                None,  # deleted_at
                None,  # deleted_by_id
                {
                    "application_type": None,
                    "date_from": "2017-06-01",
                    "date_to": "2017-06-30",
                    "case_submitted_date_from": None,
                    "case_submitted_date_to": None,
                    "case_closed_date_from": None,
                    "case_closed_date_to": None,
                },  # parameters
            ),
            (
                1002,  # id
                "IMP_DATA_EXTRACT",  # report_domain
                "Issued licences report",  # title
                "second report test",  # notes
                "",  # parameter_xml
                2,  # scheduled_by_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                dt.datetime(2022, 4, 27, 12, 23),  # started_at
                dt.datetime(2022, 4, 27, 12, 25),  # finished_at
                None,  # deleted_at
                None,  # deleted_by_id
                {
                    "application_type": None,
                    "date_from": None,
                    "date_to": None,
                    "case_submitted_date_from": "2017-06-01",
                    "case_submitted_date_to": "2017-06-30",
                    "case_closed_date_from": "2017-06-01",
                    "case_closed_date_to": "2017-06-30",
                },  # parameters
            ),
            (
                1003,  # id
                "ACCESS_REQUEST_REPORT",  # report_domain
                "Access request report",  # title
                None,  # notes
                "",  # parameter_xml
                2,  # scheduled_by_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                dt.datetime(2022, 4, 27, 12, 23),  # started_at
                dt.datetime(2022, 4, 27, 12, 25),  # finished_at
                dt.datetime(2022, 4, 30, 9, 0),  # deleted_at
                3,  # deleted_by_id
                {
                    "application_type": None,
                    "date_from": "2020-02-01",
                    "date_to": "2020-03-30",
                    "case_submitted_date_from": None,
                    "case_submitted_date_to": None,
                    "case_closed_date_from": None,
                    "case_closed_date_to": None,
                },  # parameters
            ),
            (
                1004,  # id
                "IMP_FA_SUPPLEMENTARY_REPORTS_NCA",  # report_domain
                "NCA report",  # title
                None,  # notes
                "",  # parameter_xml
                2,  # scheduled_by_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                dt.datetime(2022, 4, 27, 12, 23),  # started_at
                dt.datetime(2022, 4, 27, 12, 25),  # finished_at
                None,  # deleted_at
                None,  # deleted_by_id
                {
                    "application_type": None,
                    "date_from": "2017-06-01",
                    "date_to": "2017-06-30",
                    "case_submitted_date_from": None,
                    "case_submitted_date_to": None,
                    "case_closed_date_from": None,
                    "case_closed_date_to": None,
                },  # parameters
            ),
            (
                1005,  # id
                "IMP_FIREARMS_LICENCES",  # report_domain
                "Firearms report",  # title
                None,  # notes
                "",  # parameter_xml
                2,  # scheduled_by_id
                dt.datetime(2022, 4, 27, 12, 23),  # created_date
                dt.datetime(2022, 4, 27, 12, 23),  # started_at
                dt.datetime(2022, 4, 27, 12, 25),  # finished_at
                None,  # deleted_at
                None,  # deleted_by_id
                {
                    "application_type": None,
                    "date_from": "2023-04-10",
                    "date_to": "2023-04-20",
                    "case_submitted_date_from": None,
                    "case_submitted_date_to": None,
                    "case_closed_date_from": None,
                    "case_closed_date_to": None,
                },  # parameters
            ),
        ],
    ),
}
