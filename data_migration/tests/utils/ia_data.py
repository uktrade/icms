from datetime import datetime

from data_migration import queries

from . import xml_data as xd

IA_FILES_COLUMNS = [
    ("folder_id",),
    ("folder_type",),
    ("app_model",),
    ("target_type",),
    ("status",),
    ("target_id",),
    ("fft_id",),
    ("version_id",),
    ("created_datetime",),
    ("created_by_id",),
    ("path",),
    ("filename",),
    ("content_type",),
    ("file_size",),
]

IA_BASE_COLUMNS = [
    ("ima_id",),
    ("imad_id",),
    ("file_folder_id",),
    ("reference",),
    ("status",),
    ("submit_datetime",),
    ("create_datetime",),
    ("created",),
    ("variation_no",),
    ("licence_reference",),
    ("submitted_by_id",),
    ("created_by_id",),
    ("last_updated_by_id",),
    ("importer_id",),
    ("importer_office_legacy_id",),
    ("contact_id",),
    ("application_type_id",),
    ("process_type",),
    ("decision",),
    ("variations_xml",),
]

ia_query_result = {
    queries.section5_clauses: (
        [
            ("clause",),
            ("legacy_code",),
            ("description",),
            ("is_active",),
            ("created_datetime",),
            ("created_by_id",),
            ("updated_datetime",),
            ("updated_by_id",),
        ],
        [
            (
                "A",
                "A",
                "Aa",
                1,
                datetime(2020, 6, 29),
                2,
                None,
                None,
            ),
            (
                "B",
                "B",
                "Bb",
                1,
                datetime(2021, 5, 28),
                2,
                None,
                None,
            ),
            ("Test Clause", "5_1_ABA", "Test Description", 1, datetime.now(), 2, datetime.now(), 2),
        ],
    ),
    queries.textiles_checklist: (
        [
            ("imad_id",),
            ("case_update",),
            ("fir_required",),
            ("response_preparation",),
            ("validity_period_correct",),
            ("endorsements_listed",),
            ("authorisation",),
            ("within_maximum_amount_limit",),
        ],
        [
            (51, "N", "N/A", "true", "Y", "Y", "true", "true"),
            (52, "Y", "N", "true", "Y", "Y", None, "false"),
            (53, None, None, None, None, None, None, None),
        ],
    ),
    queries.oil_checklist: (
        [
            ("imad_id",),
            ("case_update",),
            ("fir_required",),
            ("response_preparation",),
            ("validity_period_correct",),
            ("endorsements_listed",),
            ("authorisation",),
            ("within_maximum_amount_limit",),
            ("authority_required",),
            ("authority_received",),
            ("authority_police",),
        ],
        [
            (31, "N", "N/A", "true", "Y", "Y", "true", "true", "Y", "Y", "NA"),
            (32, "Y", "N", "true", "Y", "Y", None, "false", "N", "N", "N"),
        ],
    ),
    queries.sil_checklist: (
        [
            ("imad_id",),
            ("case_update",),
            ("fir_required",),
            ("response_preparation",),
            ("validity_period_correct",),
            ("endorsements_listed",),
            ("authorisation",),
            ("within_maximum_amount_limit",),
            ("authority_required",),
            ("authority_received",),
            ("authority_police",),
            ("auth_cover_items_listed",),
            ("within_auth_restrictions",),
        ],
        [
            (11, "N", "N/A", "true", "Y", "Y", "true", "true", "Y", "Y", "NA", "Y", "Y"),
            (12, "Y", "N", "true", "Y", "Y", None, "false", "N", "N", "N", "N", "N"),
        ],
    ),
    queries.sps_docs: (
        IA_FILES_COLUMNS,
        [
            (
                100,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "priorsurveillanceapplication",  # app_model
                "IMP_SPS_DOC",  # target_type
                "RECEIVED",  # status
                1000,  # target_id
                1000,  # fft_id
                10000,  # version_id
                datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "contract/file",  # path
                "contract.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                101,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "priorsurveillanceapplication",  # app_model
                "IMP_SPS_DOC",  # target_type
                "RECEIVED",  # status
                1001,  # target_id
                1001,  # fft_id
                10001,  # version_id
                datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                "contract/file",  # path
                "contract.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
        ],
    ),
    queries.sps_application_files: (
        IA_FILES_COLUMNS,
        [
            (
                100,
                "IMP_APP_DOCUMENTS",
                "priorsurveillanceapplication",
                "IMP_SUPPORTING_DOC",
                "RECEIVED",
                1003,
                1003,
                10003,
                datetime(2022, 4, 27),
                2,
                "contract/file",
                "contract.pdf",
                "pdf",
                100,
            ),
            (
                100,
                "IMP_APP_DOCUMENTS",
                "priorsurveillanceapplication",
                "IMP_SUPPORTING_DOC",
                "RECEIVED",
                1002,
                1002,
                10002,
                datetime(2022, 4, 27),
                2,
                "contract/file",
                "contract.pdf",
                "pdf",
                100,
            ),
            (
                101,
                "IMP_APP_DOCUMENTS",
                "priorsurveillanceapplication",
                "IMP_SUPPORTING_DOC",
                "RECEIVED",
                1004,
                1004,
                10004,
                datetime(2022, 4, 27),
                2,
                "contract/file",
                "contract.pdf",
                "pdf",
                100,
            ),
        ],
    ),
    queries.fa_authorities: (
        [
            ("id",),
            ("reference",),
            ("certificate_type",),
            ("address",),
            ("postcode",),
            ("importer_id",),
            ("file_folder_id",),
        ],
        [
            (1, "A", "RFD", "123 Test", "LN1", 2, 102),
            (2, "B", "SHOTGUN", "234 Test", "LN2", 3, 103),
        ],
    ),
    queries.section5_authorities: (
        [
            ("id",),
            ("reference",),
            ("address",),
            ("postcode",),
            ("importer_id",),
            ("file_folder_id",),
        ],
        [
            (1, "A", "123 Test", "LN1", 2, 104),
            (2, "B", "234 Test", "LN2", 3, 105),
        ],
    ),
    queries.fa_certificate_files: (
        [
            ("folder_id",),
            ("folder_type",),
            ("target_type",),
            ("status",),
            ("target_id",),
            ("fft_id",),
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
                102,
                "IMP_FIREARMS_AUTHORITY_DOCS",
                "IMP_FIREARMS_AUTHORITY",
                "RECEIVED",
                1005,
                1005,
                10005,
                datetime(2022, 4, 27),
                2,
                "fa-auth/file",
                "fa-auth.pdf",
                "pdf",
                100,
            ),
            (
                103,
                "IMP_FIREARMS_AUTHORITY_DOCS",
                "IMP_FIREARMS_AUTHORITY",
                "RECEIVED",
                1006,
                1006,
                10006,
                datetime(2022, 4, 27),
                2,
                "fa-auth/file",
                "fa-auth.pdf",
                "pdf",
                100,
            ),
            (
                103,
                "IMP_FIREARMS_AUTHORITY_DOCS",
                "IMP_FIREARMS_AUTHORITY",
                "RECEIVED",
                1007,
                1007,
                10007,
                datetime(2022, 4, 27),
                2,
                "fa-auth/file",
                "fa-auth.pdf",
                "pdf",
                100,
            ),
            (
                104,
                "IMP_SECTION5_AUTHORITY_DOCS",
                "IMP_SECTION5_AUTHORITY",
                "RECEIVED",
                1008,
                1008,
                10008,
                datetime(2022, 4, 27),
                2,
                "section5-auth/file",
                "section5-auth.pdf",
                "pdf",
                100,
            ),
            (
                105,
                "IMP_SECTION5_AUTHORITY_DOCS",
                "IMP_SECTION5_AUTHORITY",
                "RECEIVED",
                1009,
                1009,
                10009,
                datetime(2022, 4, 27),
                2,
                "section5-auth/file",
                "section5-auth.pdf",
                "pdf",
                100,
            ),
        ],
    ),
    queries.fa_authority_linked_offices: (
        [("firearmsauthority_id",), ("office_legacy_id",)],
        [(1, "i-2-1"), (1, "i-2-2"), (2, "i-3-1")],
    ),
    queries.section5_linked_offices: (
        [("section5authority_id",), ("office_legacy_id",)],
        [(1, "i-2-1"), (1, "i-2-2"), (2, "i-3-1")],
    ),
    queries.ia_licence: (
        [
            ("ima_id",),
            ("imad_id",),
            ("licence_start_date",),
            ("licence_end_date",),
            ("case_reference",),
            ("is_paper_only",),
            ("status",),
            ("variation_no",),
            ("created_at",),
        ],
        [
            (
                1,  # ima_id
                11,  # imad_id
                datetime(2022, 4, 27).date(),  # licence_start_date
                datetime(2023, 4, 27).date(),  # licence_end_date
                "IMA/2022/1234",  # case_reference
                0,  # is_paper_only
                "AC",  # status
                0,  # variation_number
                datetime(2022, 4, 27, 10, 43),  # created_at
            ),
            (
                2,
                9,
                datetime(2022, 4, 27).date(),
                datetime(2023, 4, 30).date(),
                "IMA/2022/2345",
                0,
                "AR",
                0,
                datetime(2022, 4, 27, 10, 43),  # created_at
            ),
            (
                2,
                10,
                datetime(2022, 4, 27).date(),
                datetime(2023, 5, 30).date(),
                "IMA/2022/2345/1",
                0,
                "AR",
                1,
                datetime(2022, 4, 27, 10, 43),  # created_at
            ),
            (
                2,
                12,
                datetime(2022, 4, 27).date(),
                datetime(2023, 6, 30).date(),
                "IMA/2022/2345/2",
                0,
                "AC",
                2,
                datetime(2022, 4, 27, 10, 43),  # created_at
            ),
        ],
    ),
    queries.ia_licence_docs: (
        [
            ("reference",),
            ("licence_id",),
            ("document_legacy_id",),
            ("document_type",),
            ("filename",),
            ("content_type",),
            ("file_size",),
            ("path",),
            ("created_datetime",),
            ("created_by_id",),
            ("signed_datetime",),
            ("signed_by_id",),
        ],
        [
            (
                "1234A",  # reference
                11,  # licence_id
                1,  # document_legacy_id
                "LICENCE",  # document_type
                "Firearms Licence",  # filename
                "application/pdf",  # content_type
                100,  # file_size
                "firearms-licence-1.pdf",  # path
                datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                datetime(2022, 4, 27),  # signed_datetime
                2,  # signed_by
            ),
            (
                None,  # reference
                11,  # licence_id
                6,  # document_legacy_id
                "COVER_LETTER",  # document_type
                "Firearms Cover",  # filename
                "application/pdf",  # content_type
                100,  # file_size
                "firearms-cover-1.pdf",  # path
                datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                datetime(2022, 4, 27),  # signed_datetime
                2,  # signed_by
            ),
            (
                "1235B",
                9,
                2,
                "LICENCE",
                "Firearms Licence",
                "application/pdf",
                100,
                "firearms-licence-2.pdf",
                datetime(2022, 4, 27),
                2,
                datetime(2022, 4, 27),
                2,
            ),
            (
                "1236C",
                9,
                3,
                "LICENCE",
                "Firearms Licence",
                "application/pdf",
                100,
                "firearms-licence-3.pdf",
                datetime(2022, 4, 27),
                2,
                datetime(2022, 4, 27),
                2,
            ),
            (
                "1235D",
                12,
                4,
                "LICENCE",
                "Firearms Licence",
                "application/pdf",
                100,
                "firearms-licence-4.pdf",
                datetime(2022, 4, 30),
                2,
                datetime(2022, 4, 30),
                2,
            ),
            (
                "1236E",
                12,
                5,
                "LICENCE",
                "Firearms Licence",
                "application/pdf",
                100,
                "firearms-licence-5.pdf",
                datetime(2022, 4, 30),
                2,
                datetime(2022, 4, 30),
                2,
            ),
            (
                None,  # reference
                12,  # licence_id
                7,  # document_legacy_id
                "COVER_LETTER",  # document_type
                "Firearms Cover",  # filename
                "application/pdf",  # content_type
                100,  # file_size
                "firearms-cover-2.pdf",  # path
                datetime(2022, 4, 27),  # created_datetime
                2,  # created_by_id
                datetime(2022, 4, 27),  # signed_datetime
                2,  # signed_by
            ),
        ],
    ),
    queries.textiles_application_files: (
        IA_FILES_COLUMNS,
        [
            (
                41,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "textilequotaapplication",  # app_model
                "IMP_APP_DOCUMENTS",  # target_type
                "EMPTY",  # status
                5000,  # target_id
                5000,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
            (
                42,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "textilequotaapplication",  # app_model
                "IMP_APP_DOCUMENTS",  # target_type
                "EMPTY",  # status
                5001,  # target_id
                5001,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
            (
                43,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "textilequotaapplication",  # app_model
                "IMP_APP_DOCUMENTS",  # target_type
                "EMPTY",  # status
                5003,  # target_id
                5003,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
        ],
    ),
    queries.dfl_application_files: (
        IA_FILES_COLUMNS,
        [
            (
                51,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "dflapplication",  # app_model
                "IMP_SUPPORTING_DOCS",  # target_type
                "RECEIVED",  # status
                5000,  # target_id
                5000,  # fft_id
                50000,  # version_id
                datetime.now(),  # created_date
                2,  # created_by_id
                "goods/test_a.pdf",  # path
                "test_a.pdf",  # filename
                "pdf",  # content_type
                1000,  # file_size
            ),
            (
                51,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "dflapplication",  # app_model
                "IMP_SUPPORTING_DOCS",  # target_type
                "RECEIVED",  # status
                5001,  # target_id
                5001,  # fft_id
                50001,  # version_id
                datetime.now(),  # created_date
                2,  # created_by_id
                "goods/test_b.pdf",  # path
                "test_b.pdf",  # filename
                "pdf",  # content_type
                1000,  # file_size
            ),
        ],
    ),
    queries.sanction_application_files: (
        IA_FILES_COLUMNS,
        [
            (
                60,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "sanctionsapplication",  # app_model
                "IMP_SUPPORTING_DOCS",  # target_type
                "EMPTY",  # status
                6000,  # target_id
                6000,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
        ],
    ),
    queries.oil_application_files: (
        IA_FILES_COLUMNS,
        [
            (
                21,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "openindividuallicenceapplication",  # app_model
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                3000,  # target_id
                3000,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
            (
                22,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "openindividuallicenceapplication",  # app_model
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                3001,  # target_id
                3001,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
            (
                23,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "openindividuallicenceapplication",  # app_model
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                3002,  # target_id
                3002,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
        ],
    ),
    queries.sil_application_files: (
        IA_FILES_COLUMNS,
        [
            (
                1,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "silapplication",  # app_model
                "IMP_SECTION5_AUTHORITY",  # target_type
                "RECEIVED",  # status
                1000,  # target_id
                1000,  # fft_id
                10000,  # version_id
                datetime(2022, 4, 27, 12, 30),  # created_date
                2,  # created_by_id
                "contract/file",  # path
                "Test User Sec 5.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                1,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "silapplication",  # app_model
                "IMP_SECTION5_AUTHORITY",  # target_type
                "RECEIVED",  # status
                1001,  # target_id
                1001,  # fft_id
                10001,  # version_id
                datetime(2022, 3, 23, 11, 47),  # created_date
                2,  # created_by_id
                "contract/file",  # path
                "Test User Sec 5 2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                2,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "silapplication",  # app_model
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                1003,  # target_id
                1003,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
            (
                3,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "silapplication",  # app_model
                "IMP_SECTION5_AUTHORITY",  # target_type
                "EMPTY",  # status
                1004,  # target_id
                1004,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
        ],
    ),
    queries.opt_application_files: (
        IA_FILES_COLUMNS,
        [
            (
                10,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "outwardprocessingtradeapplication",  # app_model
                "IMP_SUPPORTING_DOC",  # target_type
                "RECEIVED",  # status
                2000,  # target_id
                2000,  # fft_id
                20000,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "contract/file",  # path
                "Test OPT supporting doc.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                11,  # folder_id
                "IMP_APP_DOCUMENTS",  # folder_type
                "outwardprocessingtradeapplication",  # app_model
                "IMP_SUPPORTING_DOC",  # target_type
                "RECEIVED",  # status
                2001,  # target_id
                2001,  # fft_id
                20001,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "contract/file",  # path
                "Test OPT supporting doc 2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
        ],
    ),
    queries.opt_application: (
        IA_BASE_COLUMNS
        + [
            ("customs_office_name",),
            ("customs_office_address",),
            ("rate_of_yield",),
            ("rate_of_yield_calc_method",),
            ("last_export_day",),
            ("reimport_period",),
            ("nature_process_ops",),
            ("suggested_id",),
            ("cp_origin_country_id",),
            ("cp_processing_country_id",),
            ("commodity_group_id",),
            ("cp_total_quantity",),
            ("cp_total_value",),
            ("cp_commodities_xml",),
            ("teg_origin_country_id",),
            ("teg_total_quantity",),
            ("teg_total_value",),
            ("teg_goods_description",),
            ("teg_commodities_xml",),
            ("fq_similar_to_own_factory",),
            ("fq_manufacturing_within_eu",),
            ("fq_maintained_in_eu",),
            ("fq_maintained_in_eu_r",),
            ("fq_employment_decreased",),
            ("fq_employment_decreased_r",),
            ("fq_prior_authorisation",),
            ("fq_prior_authorisation_r",),
            ("fq_past_beneficiary",),
            ("fq_past_beneficiary_r",),
            ("fq_new_application",),
            ("fq_new_application_reasons",),
            ("fq_further_authorisation",),
            ("fq_further_auth_reasons",),
            ("fq_subcontract_production",),
        ],
        [
            (
                11,  # ima_id
                21,  # imad_id
                10,  # file_folder_id
                "IMA/2022/2234",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                3456,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                3,  # application_type
                "OutwardProcessingTradeApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                "Test",  # customs_office_name
                "Test Address",  # customs_office_address
                0.5,  # rate_of_yield
                "abc",  # rate_of_yield_calc_method
                datetime(2023, 4, 23).date(),  # last_export_day
                12,  # reimport_period
                "test",  # nature_process_ops
                "test",  # suggested_id
                1,  # cp_origin_country_id
                1,  # cp_processing_country_id
                1,  # commodity_group_id
                123,  # cp_total_quantity
                100,  # cp_total_value
                xd.opt_commodities,  # cp_commodities_xml
                1,  # teg_origin_country_id
                100,  # teg_total_quantity
                500,  # teg_total_value
                "test",  # teg_goods_description
                xd.opt_commodities,  # teg_commodities_xml
                "Y",  # fq_similar_to_own_factory
                "Y",  # fq_manufacturing_within_eu
                "Y",  # fq_maintained_in_eu
                "test eu",  # fq_maintained_in_eu_r
                "N",  # fq_employment_decreased
                "test em",  # fq_employment_decreased_r
                "Y",  # fq_prior_authorisation
                "test pa",  # fq_prior_authorisation_r
                "Y",  # fq_past_beneficiary
                "test pb",  # fq_past_beneficiary_r
                "Y",  # fq_new_application
                "test na",  # fq_new_application_reasons
                "Y",  # fq_further_authorisation
                "test fa",  # fq_further_auth_reasons
                "Y",  # fq_subcontract_production
            ),
            (
                12,  # ima_id
                22,  # imad_id
                11,  # file_folder_id
                "IMA/2022/2235",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                3456,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                3,  # application_type
                "OutwardProcessingTradeApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                "Test",  # customs_office_name
                "Test Address",  # customs_office_address
                0.5,  # rate_of_yield
                "abc",  # rate_of_yield_calc_method
                datetime(2023, 4, 23).date(),  # last_export_day
                12,  # reimport_period
                "test",  # nature_process_ops
                "test",  # suggested_id
                1,  # cp_origin_country_id
                1,  # cp_processing_country_id
                1,  # commodity_group_id
                None,  # cp_total_quantity
                None,  # cp_total_value
                None,  # cp_commodities_xml
                1,  # teg_origin_country_id
                None,  # teg_total_quantity
                None,  # teg_total_value
                None,  # teg_goods_description
                None,  # teg_commodities_xml
                "N",  # fq_similar_to_own_factory
                "N",  # fq_manufacturing_within_eu
                "N",  # fq_maintained_in_eu
                None,  # fq_maintained_in_eu_r
                "N",  # fq_employment_decreased
                None,  # fq_employment_decreased_r
                "N",  # fq_prior_authorisation
                None,  # fq_prior_authorisation_r
                "N",  # fq_past_beneficiary
                None,  # fq_past_beneficiary_r
                "N",  # fq_new_application
                None,  # fq_new_application_reasons
                "N",  # fq_further_authorisation
                None,  # fq_further_auth_reasons
                "N",  # fq_subcontract_production
            ),
        ],
    ),
    queries.sanctions_application: (
        IA_BASE_COLUMNS
        + [
            ("exporter_name",),
            ("exporter_address",),
            ("commodities_xml",),
            ("sanction_emails_xml",),
        ],
        [
            (
                60,  # ima_id
                70,  # imad_id
                60,  # file_folder_id
                "IMA/2022/6234",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                6234,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                12,  # application_type
                "SanctionsApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                "Test Exporter",  # exporter_name
                "123 Somewhere",  # exporter_address
                xd.sanctions_commodities,  # commodities_xml
                xd.sanctions_emails,  # sanction_emails_xml
            )
        ],
    ),
    queries.sps_application: (
        IA_BASE_COLUMNS
        + [
            ("quantity",),
            ("value_gbp",),
            ("value_eur",),
            ("file_type",),
            ("target_id",),
        ],
        [
            (
                100,  # ima_id
                1110,  # imad_id
                100,  # file_folder_id
                "IMA/2022/10234",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                10234,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "PriorSurveillanceApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                "NONSENSE",  # quantity
                "NONSENSE",  # value_gbp
                "NONSENSE",  # value_eur
                "PRO_FORMA_INVOICE",  # file_type
                1000,  # target_id
            ),
            (
                101,  # ima_id
                1111,  # imad_id
                101,  # file_folder_id
                "IMA/2022/10235",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                10235,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "PriorSurveillanceApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                100,  # quantity
                100,  # value_gbp
                100,  # value_eur
                "SUPPLY_CONTRACT",  # file_type
                1001,  # target_id
            ),
        ],
    ),
    queries.textiles_application: (
        IA_BASE_COLUMNS,
        [
            (
                41,  # ima_id
                51,  # imad_id
                41,  # file_folder_id
                "IMA/2022/4234",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                4234,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "TexilesQuotaApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
            ),
            (
                42,  # ima_id
                52,  # imad_id
                42,  # file_folder_id
                "IMA/2022/4235",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                4235,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "TexilesQuotaApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
            ),
            (
                43,  # ima_id
                53,  # imad_id
                43,  # file_folder_id
                "IMA/2022/4236",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                4236,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "TexilesQuotaApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
            ),
        ],
    ),
    queries.dfl_application: (
        IA_BASE_COLUMNS
        + [
            ("deactivated_firearm",),
            ("proof_checked",),
            ("constabulary_id",),
            ("supplementary_report_xml",),
            ("fa_goods_certs_xml",),
        ],
        [
            (
                51,  # ima_id
                61,  # imad_id
                51,  # file_folder_id
                "IMA/2022/5234",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                5234,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                10,  # application_type
                "DFLApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                True,  # deactivated_firearm
                True,  # proof_checked
                1,  # constabulary_id
                xd.dfl_sr,  # supplementary_report_xml
                xd.dfl_goods_cert,  # fa_goods_cert_xml
            )
        ],
    ),
    queries.oil_application: (
        IA_BASE_COLUMNS
        + [
            ("section1",),
            ("section2",),
            ("bought_from_details_xml",),
            ("supplementary_report_xml",),
        ],
        [
            (
                21,  # ima_id
                31,  # imad_id
                21,  # file_folder_id
                "IMA/2022/3234",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                3234,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                5,  # application_type
                "OpenIndividualLicenceApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                1,  # section1
                1,  # section2
                None,  # bought_from_details_xml
                xd.sr_upload_xml,  # supplementary_report_xml
            ),
            (
                22,  # ima_id
                32,  # imad_id
                22,  # file_folder_id
                "IMA/2022/3235",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                3235,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                5,  # application_type
                "OpenIndividualLicenceApplication",  # process_type
                "REFUSE",  # decision
                None,  # variations_xml
                1,  # section1
                0,  # section2
                xd.import_contact_xml,  # bought_from_details_xml
                xd.sr_manual_xml,  # supplementary_report_xml
            ),
        ],
    ),
    queries.sil_application: (
        IA_BASE_COLUMNS
        + [
            ("section1",),
            ("section2",),
            ("section5",),
            ("section58_obsolete",),
            ("section58_other",),
            ("bought_from_details_xml",),
            ("supplementary_report_xml",),
            ("commodities_xml",),
            ("last_updated_datetime",),
        ],
        [
            (
                1,  # ima_id
                11,  # imad_id
                1,  # file_folder_id
                "IMA/2022/1234",  # reference
                "PROCESSING",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22, 9, 23, 22),  # create_datetime
                datetime(2022, 4, 22, 9, 23, 22),  # created
                0,  # vartiation_no
                5678,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                6,  # application_type
                "SILApplication",  # process_type
                "APPROVE",  # decision
                None,  # variations_xml
                1,  # section1
                1,  # section2
                1,  # section5
                1,  # section58_obsolete
                1,  # section58_other
                None,  # bought_from_details_xml
                xd.sr_manual_xml_5_goods,  # supplementary_report_xml
                xd.sil_goods,  # commodities_xml
            ),
            (
                2,  # ima_id
                12,  # imad_id
                2,  # file_folder_id
                "IMA/2022/2345",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22, 8, 44, 44),  # create_datetime
                datetime(2022, 4, 22, 8, 44, 44),  # created
                0,  # vartiation_no
                8901,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                None,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                6,  # application_type
                "SILApplication",  # process_type
                "APPROVE",  # decision
                xd.open_variation,  # variations_xml
                1,  # section1
                1,  # section2
                1,  # section5
                1,  # section58_obsolete
                1,  # section58_other
                xd.import_contact_xml,  # bought_from_details_xml
                xd.sr_upload_xml,  # supplementary_report_xml
                xd.sil_goods_sec_1,  # commodities_xml
            ),
            (
                3,  # ima_id
                13,  # imad_id
                3,  # file_folder_id
                "IMA/2022/2346",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22, 7, 52, 4),  # create_datetime
                datetime(2022, 4, 22, 7, 52, 4),  # created
                0,  # vartiation_no
                8901,  # licence_reference
                2,  # submitted_by_id
                2,  # created_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                6,  # application_type
                "SILApplication",  # process_type
                "APPROVE",  # decision
                xd.open_variation,  # variations_xml
                1,  # section1
                0,  # section2
                0,  # section5
                1,  # section58_obsolete
                0,  # section58_other
                xd.import_contact_xml,  # bought_from_details_xml
                xd.sr_manual_xml_legacy,  # supplementary_report_xml
                xd.sil_goods_legacy,  # commodities_xml
            ),
        ],
    ),
    queries.ia_type: (
        [
            ("id",),
            ("is_active",),
            ("type",),
            ("sub_type",),
            ("licence_type_code",),
            ("sigl_flag",),
            ("chief_flag",),
            ("chief_licence_prefix",),
            ("paper_licence_flag",),
            ("electronic_licence_flag",),
            ("cover_letter_flag",),
            ("cover_letter_schedule_flag",),
            ("category_flag",),
            ("default_licence_length_months",),
            ("quantity_unlimited_flag",),
            ("exp_cert_upload_flag",),
            ("supporting_docs_upload_flag",),
            ("multiple_commodities_flag",),
            ("guidance_file_url",),
            ("usage_auto_category_desc_flag",),
            ("case_checklist_flag",),
            ("importer_printable",),
            ("commodity_type_id",),
            ("consignment_country_group_id",),
            ("declaration_template_mnem",),
            ("default_commodity_group_id",),
            ("master_country_group_id",),
            ("origin_country_group_id",),
        ],
        [
            (
                1,  # id
                0,  # is_active
                "TEX",  # type
                "QUOTA",  # sub_type
                "QUOTA",  # licence_type_code
                "true",  # sigl_flag
                "true",  # chief_flag
                "GBTEX",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "false",  # electronic_licence_flag
                "false",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "false",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "true",  # supporting_docs_upload_flag
                "false",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidence_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_A",  # commodity_type_id
                "A",  # consignment_country_group_id
                "IMA_GEN_DECLARATION",  # declaration_template_mnem
                None,  # default_commodity_group_id
                None,  # master_country_group_id
                "A",  # origin_country_group_id
            ),
            (
                3,  # id
                0,  # is_active
                "OPT",  # type
                "QUOTA",  # sub_type
                "OPT",  # licence_type_code
                "true",  # sigl_flag
                "false",  # chief_flag
                None,  # chief_licence_prefix
                "true",  # paper_licence_flag
                "false",  # electronic_licence_flag
                "false",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                9,  # default_licence_length_months
                "false",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "true",  # supporting_docs_upload_flag
                "false",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidence_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_A",  # commodity_type_id
                "A",  # consignment_country_group_id
                "IMA_OPT_DECLARATION",  # declaration_template_mnem
                None,  # default_commodity_group_id
                None,  # master_country_group_id
                "A",  # origin_country_group_id
            ),
            (
                4,  # id
                0,  # is_active
                "SAN",  # type
                "SAN1",  # sub_type
                "SANCTIONS",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBSAN",  # chief_licence_prefix
                "false",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "false",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                None,  # default_licence_length_months
                "false",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "true",  # supporting_docs_upload_flag
                "false",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidence_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                None,  # commodity_type_id
                "A",  # consignment_country_group_id
                "IMA_GEN_DECLARATION",  # declaration_template_mnem
                None,  # default_commodity_group_id
                None,  # master_country_group_id
                "A",  # origin_country_group_id
            ),
            (
                5,  # id
                1,  # is_active
                "FA",  # type
                "OIL",  # sub_type
                "FIREARMS",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBOIL",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "true",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "true",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "false",  # supporting_docs_upload_flag
                "true",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_B",  # commodity_type_id
                "A",  # consignment_country_group_id
                "IMA_GEN_DECLARATION",  # declaration_template_mnem
                None,  # default_commodity_group_id
                "A",  # master_country_group_id
                "A",  # origin_country_group_id
            ),
            (
                6,  # id
                1,  # is_active
                "FA",  # type
                "SIL",  # sub_type
                "FIREARMS",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBSIL",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "true",  # cover_letter_flag
                "true",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "false",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "false",  # supporting_docs_upload_flag
                "true",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_B",  # commodity_type_id
                "A",  # consignment_country_group_id
                "IMA_GEN_DECLARATION",  # declaration_template_mnem
                None,  # default_commodity_group_id
                "A",  # master_country_group_id
                "A",  # origin_country_group_id
            ),
            (
                9,  # id
                1,  # is_active
                "WD",  # type
                "QUOTA",  # sub_type
                "WOOD",  # licence_type_code
                "true",  # sigl_flag
                "false",  # chief_flag
                None,  # chief_licence_prefix
                "true",  # paper_licence_flag
                "false",  # electronic_licence_flag
                "false",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "false",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "true",  # supporting_docs_upload_flag
                "false",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidence_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_A",  # commodity_type_id
                "A",  # consignment_country_group_id
                "IMA_GEN_DECLARATION",  # declaration_template_mnem
                None,  # default_commodity_group_id
                None,  # master_country_group_id
                "A",  # origin_country_group_id
            ),
            (
                10,  # id
                1,  # is_active
                "FA",  # type
                "DFL",  # sub_type
                "FIREARMS",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBDFL",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "true",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "true",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "false",  # supporting_docs_upload_flag
                "true",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_B",  # commodity_type_id
                "A",  # consignment_country_group_id
                "IMA_GEN_DECLARATION",  # declaration_template_mnem
                None,  # default_commodity_group_id
                "A",  # master_country_group_id
                "A",  # origin_country_group_id
            ),
            (
                11,  # id
                0,  # is_active
                "SPS",  # type
                "SPS1",  # sub_type
                "SURVEILLANCE",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBAOG",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "true",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "true",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "false",  # supporting_docs_upload_flag
                "true",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_B",  # commodity_type_id
                "A",  # consignment_country_group_id
                "IMA_GEN_DECLARATION",  # declaration_template_mnem
                None,  # default_commodity_group_id
                "A",  # master_country_group_id
                "A",  # origin_country_group_id
            ),
            (
                12,  # id
                0,  # is_active
                "ADHOC",  # type
                "ADHOC1",  # sub_type
                "ADHOC",  # licence_type_code
                "false",  # sigl_flag
                "true",  # chief_flag
                "GBSAN",  # chief_licence_prefix
                "true",  # paper_licence_flag
                "true",  # electronic_licence_flag
                "true",  # cover_letter_flag
                "false",  # cover_letter_schedule_flag
                "true",  # category_flag
                6,  # default_licence_length_months
                "true",  # quantity_unlimited_flag
                "false",  # exp_cert_upload_flag
                "false",  # supporting_docs_upload_flag
                "true",  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                "false",  # usage_auto_category_desc_flag
                "true",  # case_checklist_flag
                "false",  # importer_printable
                "TYPE_B",  # commodity_type_id
                "A",  # consignment_country_group_id
                "IMA_GEN_DECLARATION",  # declaration_template_mnem
                None,  # default_commodity_group_id
                "A",  # master_country_group_id
                "A",  # origin_country_group_id
            ),
        ],
    ),
    queries.constabulary_emails: (
        [
            ("ima_id",),
            ("status",),
            ("to",),
            ("cc_address_list_str",),
            ("subject",),
            ("body",),
        ],
        [
            (
                1,  # ima_id
                "DRAFT",  # status
                None,  # to
                None,  # cc_address_list_str
                None,  # subject
                None,  # body
            ),
            (
                1,  # ima_id
                "OPEN",  # status
                "a@example.com",  # to /PS-IGNORE
                "b@example.com;c@example.com",  # cc_address_list_str /PS-IGNORE
                "test a",  # subject
                "test a body",  # body
            ),
            (
                1,  # ima_id
                "CLOSED",  # status
                "a@example.com",  # to /PS-IGNORE
                "b@example.com",  # cc_address_list_str /PS-IGNORE
                "test b",  # subject
                "test b body",  # body
            ),
        ],
    ),
    queries.case_note: (
        [
            ("ima_id",),
            ("status",),
            ("note",),
            ("created_by_id",),
            ("create_datetime",),
            ("file_folder_id",),
        ],
        [
            (1, "OPEN", "Some note", 2, "2020-01-01T11:12:13", 10),
            (2, "CLOSED", "Some other note", 2, "2021-02-02T12:13:14", 11),
            (2, "DRAFT", "Some draft note", 2, "2022-03-03T13:14:15", 12),
        ],
    ),
    queries.case_note_files: (
        IA_FILES_COLUMNS,
        [
            (
                10,  # folder_id
                "IMP_CASE_NOTE_DOCUMENTS",  # folder_type
                "",  # app_model
                "CASE_NOTE_DOCUMENT",  # target_type
                "RECEIVED",  # status
                2000,  # target_id
                2000,  # fft_id
                20000,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "case_note/file1",  # path
                "Test Case Note 1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                10,  # folder_id
                "IMP_CASE_NOTE_DOCUMENTS",  # folder_type
                "",  # app_model
                "CASE_NOTE_DOCUMENT",  # target_type
                "RECEIVED",  # status
                2001,  # target_id
                2001,  # fft_id
                20001,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "case_note/file2",  # path
                "Test Case Note 2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                11,  # folder_id
                "IMP_CASE_NOTE_DOCUMENTS",  # folder_type
                "",  # app_model
                "CASE_NOTE_DOCUMENT",  # target_type
                "RECEIVED",  # status
                2003,  # target_id
                2003,  # fft_id
                20003,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "case_note/file3",  # path
                "Test Case Note 3.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                12,  # folder_id
                "IMP_CASE_NOTE_DOCUMENTS",  # folder_type
                "",  # app_model
                "CASE_NOTE_DOCUMENT",  # target_type
                "EMPTY",  # status
                2004,  # target_id
                2004,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
        ],
    ),
    queries.update_request: (
        [
            ("ima_id",),
            ("status",),
            ("request_subject",),
            ("request_detail",),
            ("response_details",),
            ("request_datetime",),
            ("request_by_id",),
            ("response_datetime",),
            ("response_by_id",),
            ("closed_datetime",),
            ("closed_by_id",),
        ],
        [
            (
                1,  # ima_id
                "CLOSED",  # status
                "Test Closed",  # request_subject
                "Closed Details",  # request_detail
                "AA",  # response_detail
                datetime(2021, 1, 2),  # request_datetime
                2,  # request_by_id
                datetime(2021, 1, 3),  # response_datetime
                2,  # response_by_id
                datetime(2021, 1, 4),  # closed_datetime
                2,  # closed_by_id
            ),
            (
                1,  # ima_id
                "OPEN",  # status
                "Test Open",  # request_subject
                "Open Details",  # request_detail
                None,  # response_detail
                datetime(2021, 2, 2),  # request_datetime
                2,  # request_by_id
                None,  # response_datetime
                None,  # response_by_id
                None,  # closed_datetime
                None,  # closed_by_id
            ),
            (
                1,  # ima_id
                "DRAFT",  # status
                None,  # request_subject
                None,  # request_detail
                None,  # response_detail
                None,  # request_datetime
                None,  # request_by_id
                None,  # response_datetime
                None,  # response_by_id
                None,  # closed_datetime
                None,  # closed_by_id
            ),
        ],
    ),
    queries.fir: (
        [
            ("ia_ima_id",),
            ("status",),
            ("request_subject",),
            ("request_detail",),
            ("response_details",),
            ("requested_datetime",),
            ("request_by_id",),
            ("response_datetime",),
            ("response_by_id",),
            ("closed_datetime",),
            ("closed_by_id",),
            ("folder_id",),
            ("email_cc_address_list_str",),
            ("process_type",),
            ("created",),
        ],
        [
            (
                1,  # ia_ima_id
                "CLOSED",  # status
                "Test Closed",  # request_subject
                "Closed Details",  # request_detail
                "AA",  # response_detail
                datetime(2021, 1, 2, 12, 23),  # requested_datetime
                2,  # request_by_id
                datetime(2021, 1, 3, 13, 23),  # response_datetime
                2,  # response_by_id
                datetime(2021, 1, 4, 13, 23),  # closed_datetime
                2,  # closed_by_id
                20,  # folder_id
                "b@example.com;c@example.com",  # email_cc_address_list_str /PS-IGNORE
                "FurtherInformationRequest",  # process_type
                datetime(2021, 1, 2, 12, 23),  # created
            ),
            (
                1,  # ia_ima_id
                "RESPONDED",  # status
                "Test Responded",  # request_subject
                "Responded Details",  # request_detail
                "BB",  # response_detail
                datetime(2021, 1, 2, 12, 23),  # requested_datetime
                2,  # request_by_id
                datetime(2021, 1, 3, 13, 23),  # response_datetime
                2,  # response_by_id
                None,  # closed_datetime
                None,  # closed_by_id
                21,  # folder_id
                "b@example.com",  # email_cc_address_list_str /PS-IGNORE
                "FurtherInformationRequest",  # process_type
                datetime(2021, 1, 2, 12, 23),  # created
            ),
            (
                1,  # ia_ima_id
                "OPEN",  # status
                "Test Open",  # request_subject
                "Open Details",  # request_detail
                None,  # response_detail
                datetime(2021, 2, 2, 12, 23),  # requested_datetime
                2,  # request_by_id
                None,  # response_datetime
                None,  # response_by_id
                None,  # closed_datetime
                None,  # closed_by_id
                22,  # folder_id
                None,  # email_cc_address_list_str
                "FurtherInformationRequest",  # process_type
                datetime(2021, 1, 2, 12, 23),  # created
            ),
        ],
    ),
    queries.fir_files: (
        IA_FILES_COLUMNS,
        [
            (
                20,  # folder_id
                "IMP_RFI_DOCUMENTS",  # folder_type
                None,  # app_model
                "RFI_DOCUMENT",  # target_type
                "RECEIVED",  # status
                3000,  # target_id
                3000,  # fft_id
                30000,  # version_id
                datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "fir/file1",  # path
                "Test FIR 1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                20,  # folder_id
                "IMP_RFI_DOCUMENTS",  # folder_type
                None,  # app_model
                "RFI_DOCUMENT",  # target_type
                "RECEIVED",  # status
                3001,  # target_id
                3001,  # fft_id
                30001,  # version_id
                datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "fir/file2",  # path
                "Test FIR 2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                21,  # folder_id
                "IMP_RFI_DOCUMENTS",  # folder_type
                None,  # app_model
                "RFI_DOCUMENT",  # target_type
                "RECEIVED",  # status
                3003,  # target_id
                3003,  # fft_id
                30003,  # version_id
                datetime(2022, 4, 27, 12, 23),  # created_date
                2,  # created_by_id
                "fir/file3",  # path
                "Test FIR 3.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                22,  # folder_id
                "IMP_RFI_DOCUMENTS",  # folder_type
                None,  # app_model
                "RFI_DOCUMENT",  # target_type
                "EMPTY",  # status
                3004,  # target_id
                3004,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
        ],
    ),
    queries.endorsement: (
        [
            ("imad_id",),
            ("content",),
            ("created_datetime",),
        ],
        [
            (11, "Content A", datetime(2022, 4, 27, 12, 23)),
            (11, "Content B", datetime(2022, 4, 27, 12, 23)),
        ],
    ),
    queries.sigl_transmission: (
        [
            ("ima_id",),
            ("status",),
            ("transmission_type",),
            ("request_type",),
            ("sent_datetime",),
            ("sent_by_id",),
            ("response_datetime",),
            ("response_message",),
            ("response_code",),
        ],
        [
            (
                100,  # ima_id
                "ACCEPTED",  # status
                "WEB_SERVICE",  # transmission_type
                "INSERT",  # request_type
                datetime.now(),  # sent_datetime
                2,  # sent_by_id
                datetime.now(),  # response_datetime
                "Successful processing",  # response_message
                0,  # response_code
            ),
            (
                100,  # ima_id
                "ACCEPTED",  # status
                "WEB_SERVICE",  # transmission_type
                "CONFIRM",  # request_type
                datetime.now(),  # sent_datetime
                2,  # sent_by_id
                datetime.now(),  # response_datetime
                "Successful processing",  # response_message
                0,  # response_code
            ),
            (
                100,  # ima_id
                "ACCEPTED",  # status
                "WEB_SERVICE",  # transmission_type
                "DELETE",  # request_type
                datetime.now(),  # sent_datetime
                2,  # sent_by_id
                datetime.now(),  # response_datetime
                "Successful processing",  # response_message
                0,  # response_code
            ),
            (
                101,  # ima_id
                "REJECTED",  # status
                "MANUAL",  # transmission_type
                "INSERT",  # request_type
                datetime.now(),  # sent_datetime
                2,  # sent_by_id
                datetime.now(),  # response_datetime
                "Something missing",  # response_message
                500,  # response_code
            ),
            (
                101,  # ima_id
                "ACCEPTED",  # status
                "MANUAL",  # transmission_type
                "INSERT",  # request_type
                datetime.now(),  # sent_datetime
                2,  # sent_by_id
                None,  # response_datetime
                None,  # response_message
                None,  # response_code
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
}
