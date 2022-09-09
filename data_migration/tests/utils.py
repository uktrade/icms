from datetime import datetime

from data_migration import models as dm
from data_migration.queries import (
    export_application,
    files,
    import_application,
    reference,
    user,
)
from web import models as web

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
    ("issue_date",),
    ("licence_reference",),
    ("submitted_by_id",),
    ("created_by_id",),
    ("last_updated_by_id",),
    ("importer_id",),
    ("importer_office_legacy_id",),
    ("contact_id",),
    ("application_type_id",),
    ("process_type",),
    ("variations_xml",),
]

EA_BASE_COLUMNS = [
    ("ca_id",),
    ("cad_id",),
    ("process_type",),
    ("reference",),
    ("status",),
    ("created_by_id",),
    ("create_datetime",),
    ("created",),
    ("submit_datetime",),
    ("last_updated_by_id",),
    ("last_updated_datetime",),
    ("variation_no",),
    ("application_type_id",),
    ("exporter_id",),
    ("exporter_office_legacy_id",),
]

query_result = {
    reference.country: (
        [("id",), ("name",), ("is_active",), ("type",), ("commission_code",), ("hmrc_code",)],
        [
            (1, "CA", 1, "A", 100, "CA"),
            (2, "CB", 1, "A", 101, "CB"),
            (3, "CC", 1, "B", 102, "CC"),
            (4, "CD", 0, "A", 103, "CD"),
        ],
    ),
    reference.country_group: (
        [("country_group_id",), ("name",), ("comments",)],
        [
            ("A", "TEST GROUP A", None),
            ("B", "TEST GROUP B", "Comment B"),
            ("C", "TEST GROUP C", "Comment C"),
        ],
    ),
    reference.unit: (
        [("unit_type",), ("description",), ("short_description",), ("hmrc_code",)],
        [
            ("GS", "grams", "gs", 100),
            ("KGS", "kilos", "Kgs", 101),
            ("TBS", "terrabytes", "Tbs", 102),
        ],
    ),
    reference.constabularies: (
        [("is_active",), ("name",), ("region",), ("email",)],
        [
            (1, "A", "A", "a@example.com"),  # /PS-IGNORE
            (1, "B", "B", "b@example.com"),  # /PS-IGNORE
            (1, "C", "C", "c@example.com"),  # /PS-IGNORE
        ],
    ),
    reference.obsolete_calibre_group: (
        [("legacy_id",), ("name",), ("is_active",), ("order",)],
        [
            (1, "A", 1, 1),
            (2, "B", 1, 2),
            (3, "C", 1, 3),
        ],
    ),
    import_application.section5_clauses: (
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
            (
                "C",
                "C",
                "Cc",
                1,
                datetime(2022, 4, 27),
                2,
                None,
                None,
            ),
        ],
    ),
    import_application.textiles_checklist: (
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
            (1234, "N", "N/A", "true", "Y", "Y", "true", "true"),
            (1235, "Y", "N", "true", "Y", "Y", None, "false"),
            (1236, None, None, None, None, None, None, None),
        ],
    ),
    import_application.oil_checklist: (
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
            (1000, "N", "N/A", "true", "Y", "Y", "true", "true", "Y", "Y", "NA"),
            (1001, "Y", "N", "true", "Y", "Y", None, "false", "N", "N", "N"),
        ],
    ),
    import_application.sil_checklist: (
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
    files.sps_application_files: (
        IA_FILES_COLUMNS,
        [
            (
                100,
                "IMP_APP_DOCUMENTS",
                "priorsurveillanceapplication",
                "IMP_SPS_DOC",
                "RECEIVED",
                1000,
                1000,
                10000,
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
                "IMP_SPS_DOC",
                "RECEIVED",
                1001,
                1001,
                10001,
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
    import_application.fa_authorities: (
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
    import_application.section5_authorities: (
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
    files.fa_certificate_files: (
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
    user.importers: (
        [
            ("id",),
            ("is_active",),
            ("type",),
            ("name",),
            ("registered_number",),
            ("eori_number",),
            ("user_id",),
            ("main_importer_id",),
            ("region_origin",),
        ],
        [
            (1, 1, "INDIVIDUAL", None, 123, "GB123456789012", 2, None, "O"),
            (2, 1, "ORGANISATION", "Test Org", 124, "GB123456789013", 2, None, None),
            (3, 1, "INDIVIDUAL", "Test Agent", 125, "GB123456789014", 2, 2, None),
        ],
    ),
    user.importer_offices: (
        [
            ("importer_id",),
            ("legacy_id",),
            ("is_active",),
            ("postcode",),
            ("address",),
            ("eori_number",),
            ("address_entry_type",),
        ],
        [
            (2, "i-2-1", 1, "ABC", "123 Test\nTest City", "GB123456789015", "SEARCH"),
            (2, "i-2-2", 1, "DEF", "456 Test", "GB123456789016", "MANUAL"),
            (
                3,
                "i-3-1",
                1,
                "deletethisTESTLONG",
                "ABC Test\nTest Town\nTest City",
                "GB123456789017",
                "MANUAL",
            ),
        ],
    ),
    user.exporters: (
        [
            ("id",),
            ("is_active",),
            ("name",),
            ("registered_number",),
            ("main_importer_id",),
        ],
        [
            (1, 1, "Test Org", 123, 2, None),
            (2, 1, "Test Agent", 124, "GB123456789013", 2, 1),
            (3, 0, "Test Inactive", 125, "GB123456789014", 2, None),
        ],
    ),
    user.exporter_offices: (
        [
            ("exporter_id",),
            ("legacy_id",),
            ("is_active",),
            ("postcode",),
            ("address",),
            ("address_entry_type",),
        ],
        [
            (2, "e-2-1", 1, "Exp A", "123 Test\nTest City", "SEARCH"),
            (2, "e-2-2", 1, "Very Long Postcode", "456 Test", "MANUAL"),
            (
                3,
                "e-3-1",
                0,
                "TEST",
                "ABC Test\nTest Town\nTest City",
                "MANUAL",
            ),
        ],
    ),
    import_application.fa_authority_linked_offices: (
        [("firearmsauthority_id",), ("office_legacy_id",)],
        [(1, "i-2-1"), (1, "i-2-2"), (2, "i-3-1")],
    ),
    import_application.section5_linked_offices: (
        [("section5authority_id",), ("office_legacy_id",)],
        [(1, "i-2-1"), (1, "i-2-2"), (2, "i-3-1")],
    ),
    import_application.ia_licence: (
        [
            ("ima_id",),
            ("imad_id",),
            ("licence_start_date",),
            ("licence_end_date",),
            ("case_reference",),
            ("is_paper_only",),
            ("status",),
            ("variation_no",),
        ],
        [
            (
                1,  # ima_id
                11,  # imad_id
                datetime(2022, 4, 27).date(),  # licence_start_date
                datetime(2023, 4, 27).date(),  # licence_end_date
                "IMA/2022/1234",  # case_reference
                0,  # is_paper_only
                "AC",
                0,
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
            ),
        ],
    ),
    import_application.ia_licence_docs: (
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
    files.sil_application_files: (
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
                datetime(2022, 4, 27),  # created_date
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
                datetime(2022, 4, 27),  # created_date
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
        ],
    ),
    import_application.sil_application: (
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
        ],
        [
            (
                1,  # ima_id
                11,  # imad_id
                1,  # file_folder_id
                "IMA/2022/1234",  # reference
                "COMPLETE",  # status
                datetime(2022, 4, 23),  # submit_datetime
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                datetime(2022, 4, 24),  # issue_date
                5678,  # licence_reference
                2,  # submitted_by_id
                2,  # creeated_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "SILApplication",  # process_type
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
                datetime(2022, 4, 22),  # create_datetime
                datetime(2022, 4, 22),  # created
                0,  # vartiation_no
                datetime(2022, 4, 24),  # issue_date
                8901,  # licence_reference
                2,  # submitted_by_id
                2,  # creeated_by_id
                2,  # last_updated_by_id
                2,  # importer_id
                "i-2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "SILApplication",  # process_type
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
        ],
    ),
    import_application.ia_type: (
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
                1,  # is_active
                "FA",  # type
                "SIL",  # sub_type
                "FIREARMS",  # licence_type_code
                False,  # sigl_flag
                True,  # chief_flag
                "GBSIL",  # chief_licence_prefix
                True,  # paper_licence_flag
                True,  # electronic_licence_flag
                True,  # cover_letter_flag
                True,  # cover_letter_schedule_flag
                True,  # category_flag
                6,  # default_licence_length_months
                False,  # quantity_unlimited_flag
                False,  # exp_cert_upload_flag
                False,  # supporting_docs_upload_flag
                True,  # multiple_commodities_flag
                "/docs/file.pdf",  # guidance_file_url
                False,  # usage_auto_category_desc_flag
                True,  # case_checklist_flag
                False,  # importer_printable
                None,  # commodity_type_id
                "A",  # consignment_country_group_id
                "IMA_GEN_DECLARATION",  # declaration_template_mnem
                None,  # default_commodity_group_id
                "A",  # master_country_group_id
                "A",  # origin_country_group_id
            )
        ],
    ),
    import_application.constabulary_emails: (
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
    import_application.case_note: (
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
    files.case_note_files: (
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
    import_application.update_request: (
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
    import_application.fir: (
        [
            ("ia_ima_id",),
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
            ("folder_id",),
            ("email_cc_address_list_str",),
            ("process_type",),
        ],
        [
            (
                1,  # ia_ima_id
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
                20,  # folder_id
                "b@example.com;c@example.com",  # email_cc_address_list_str /PS-IGNORE
                "FurtherInformationRequest",  # process_type
            ),
            (
                1,  # ia_ima_id
                "RESPONDED",  # status
                "Test Responded",  # request_subject
                "Responded Details",  # request_detail
                "BB",  # response_detail
                datetime(2021, 1, 2),  # request_datetime
                2,  # request_by_id
                datetime(2021, 1, 3),  # response_datetime
                2,  # response_by_id
                None,  # closed_datetime
                None,  # closed_by_id
                21,  # folder_id
                "b@example.com",  # email_cc_address_list_str /PS-IGNORE
                "FurtherInformationRequest",  # process_type
            ),
            (
                1,  # ia_ima_id
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
                22,  # folder_id
                None,  # email_cc_address_list_str
                "FurtherInformationRequest",  # process_type
            ),
        ],
    ),
    files.fir_files: (
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
                datetime(2022, 4, 27),  # created_date
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
                datetime(2022, 4, 27),  # created_date
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
                datetime(2022, 4, 27),  # created_date
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
    import_application.endorsement: (
        [("imad_id",), ("content",)],
        [(11, "Content A"), (11, "Content B")],
    ),
    export_application.product_legislation: (
        [
            ("id",),
            ("name",),
            ("is_active",),
            ("is_biocidal",),
            ("is_biocidal_claim",),
            ("is_eu_cosmetics_regulation",),
            ("gb_legislation",),
            ("ni_legislation",),
        ],
        [
            (
                1,  # id
                "Test",  # name
                1,  # is_active
                0,  # is_biocidal
                0,  # is_biocidal_claim
                1,  # is_eu_cosmetics_regulation
                1,  # gb_legislation
                1,  # ni_legislation
            ),
            (
                2,  # id
                "Test Biocide",  # name
                1,  # is_active
                1,  # is_biocidal
                0,  # is_biocidal_claim
                0,  # is_eu_cosmetics_regulation
                1,  # gb_legislation
                0,  # ni_legislation
            ),
            (
                3,  # id
                "Test Inactive",  # name
                0,  # is_active
                0,  # is_biocidal
                0,  # is_biocidal_claim
                0,  # is_eu_cosmetics_regulation
                0,  # gb_legislation
                1,  # ni_legislation
            ),
        ],
    ),
    export_application.export_application_type: (
        [
            ("id",),
            ("is_active",),
            ("type_code",),
            ("type",),
            ("allow_multiple_products",),
            ("generate_cover_letter",),
            ("allow_hse_authorization",),
            ("country_group_legacy_id",),
            ("country_of_manufacture_cg_id"),
        ],
        [
            (1, 1, "CFS", "Certificate of Free Sale", 1, 0, 0, "A", None),
            (2, 1, "COM", "Certificate of Manufacture", 0, 0, 0, "B", None),
            (21, 1, "GMP", "Certificate of Good Manufacturing Practice", 1, 0, 0, "C", None),
        ],
    ),
    files.gmp_files: (
        IA_FILES_COLUMNS,
        [
            (
                31,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "ISO17021",  # target_type
                "EMPTY",  # status
                4000,  # target_id
                4000,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
            (
                32,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "ISO17065",  # target_type
                "RECEIVED",  # status
                4001,  # target_id
                4001,  # fft_id
                40001,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp2/ISO17065",  # path
                "ISO17065.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                32,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "ISO22716",  # target_type
                "RECEIVED",  # status
                4002,  # target_id
                4002,  # fft_id
                40002,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp2/ISO22716",  # path
                "ISO22716.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                32,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "ISO17021",  # target_type
                "EMPTY",  # status
                4003,  # target_id
                4003,  # fft_id
                None,  # version_id
                None,  # created_date
                None,  # created_by_id
                None,  # path
                None,  # filename
                None,  # content_type
                None,  # file_size
            ),
            (
                33,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "ISO17021",  # target_type
                "RECEIVED",  # status
                4004,  # target_id
                4004,  # fft_id
                40004,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp3/ISO17021",  # path
                "ISO17021.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
            (
                31,  # folder_id
                "GMP_SUPPORTING_DOCUMENTS",  # folder_type
                None,  # app_model
                "BRCGS",  # target_type
                "RECEIVED",  # status
                4005,  # target_id
                4005,  # fft_id
                40005,  # version_id
                datetime(2022, 4, 27),  # created_date
                2,  # created_by_id
                "gmp1/BRCGS",  # path
                "BRCGS.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
            ),
        ],
    ),
    export_application.gmp_application: (
        EA_BASE_COLUMNS
        + [
            ("brand_name",),
            ("file_folder_id",),
        ],
        [
            (
                7,  # ca_id
                17,  # cad_id
                "CertificateofGoodManufacturingPractice",  # process_type
                "CA/2022/9901",  # reference
                "IN PROGRESS",  # status
                2,  # created_by_id
                datetime(2022, 4, 27),  # create_datetime
                datetime(2022, 4, 27),  # created
                None,  # submit_datetime
                2,  # last_updated_by_id
                datetime(2022, 4, 27),  # last_updated_datetime
                0,  # variation_no
                21,  # application_type_id
                2,  # exporter_id
                "e-2-1",  # export_office_legacy_id
                None,  # brand_name
                31,  # file_folder_id
            ),
            (
                8,
                18,
                "CertificateofGoodManufacturingPractice",
                "CA/2022/9902",
                "PROCESSING",
                2,
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
                0,
                21,
                3,
                "e-3-1",
                "A brand",
                32,
            ),
            (
                9,
                19,
                "CertificateofGoodManufacturingPractice",
                "CA/2022/9903",
                "COMPLETED",
                2,
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
                0,
                21,
                2,
                "e-2-2",
                "Another brand",
                33,
            ),
        ],
    ),
    export_application.export_application_countries: (
        [("cad_id",), ("country_id",)],
        [(18, 1), (18, 2), (18, 3), (19, 1), (21, 1), (22, 1), (24, 1), (25, 1)],
    ),
    export_application.com_application: (
        EA_BASE_COLUMNS
        + [
            ("is_pesticide_on_free_sale_uk",),
            ("is_manufacturer",),
            ("product_name",),
            ("chemical_name",),
            ("manufacturing_process",),
        ],
        [
            (
                10,  # ca_id
                20,  # cad_id
                "CertificateOfManufactureApplication",  # process_type
                "CA/2022/9904",  # reference
                "IN PROGRESS",  # status
                2,  # created_by_id
                datetime(2022, 4, 27),  # create_datetime
                datetime(2022, 4, 27),  # created
                None,  # submit_datetime
                2,  # last_updated_by_id
                datetime(2022, 4, 27),  # last_updated_datetime
                0,  # variation_no
                2,  # application_type_id
                2,  # exporter_id
                "e-2-1",  # export_office_legacy_id
                None,  # is_pesticide_on_free_sale_uk
                None,  # is_manufacturer
                None,  # product_name
                None,  # chemical_name
                None,  # manufacturing_process
            ),
            (
                11,
                21,
                "CertificateOfManufactureApplication",
                "CA/2022/9905",
                "PROCESSING",
                2,
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
                0,
                2,
                3,
                "e-3-1",
                1,  # is_pesticide_on_free_sale_uk
                0,  # is_manufacturer
                "A product",  # product_name
                "A chemical",  # chemical_name
                "Test",  # manufacturing_process
            ),
            (
                12,
                22,
                "CertificateOfManufactureApplication",
                "CA/2022/9906",
                "COMPLETED",
                2,
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
                0,
                2,
                2,
                "e-2-2",
                0,  # is_pesticide_on_free_sale_uk
                1,  # is_manufacturer
                "Another product",  # product_name
                "Another chemical",  # chemical_name
                "Test process",  # manufacturing_process
            ),
        ],
    ),
    export_application.cfs_application: (
        EA_BASE_COLUMNS,
        [
            (
                13,  # ca_id
                23,  # cad_id
                "CertificateOfFreeSaleApplication",  # process_type
                "CA/2022/9907",  # reference
                "IN PROGRESS",  # status
                2,  # created_by_id
                datetime(2022, 4, 27),  # create_datetime
                datetime(2022, 4, 27),  # created
                None,  # submit_datetime
                2,  # last_updated_by_id
                datetime(2022, 4, 27),  # last_updated_datetime
                0,  # variation_no
                2,  # application_type_id
                2,  # exporter_id
                "e-2-1",  # export_office_legacy_id
            ),
            (
                14,
                24,
                "CertificateOfFreeSaleApplication",  # process_type
                "CA/2022/9908",
                "PROCESSING",
                2,
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
                0,
                2,
                3,
                "e-3-1",
            ),
            (
                15,
                25,
                "CertificateOfFreeSaleApplication",  # process_type
                "CA/2022/9909",
                "COMPLETED",
                2,
                datetime(2022, 4, 28),
                datetime(2022, 4, 28),
                datetime(2022, 4, 29),
                2,
                datetime(2022, 4, 29),
                0,
                2,
                2,
                "e-2-2",
            ),
        ],
    ),
    export_application.cfs_schedule: (
        [
            ("cad_id",),
            ("schedule_ordinal",),
            ("exporter_status",),
            ("brand_name_holder",),
            ("product_eligibility",),
            ("goods_placed_on_uk_market",),
            ("goods_export_only",),
            ("any_raw_materials",),
            ("final_product_end_use",),
            ("country_of_manufacture_id",),
            ("accordance_with_standards",),
            ("is_responsible_person",),
            ("manufacturer_name",),
            ("manufacturer_address_type",),
            ("created_by_id",),
            ("product_xml",),
            ("legislation_xml",),
        ],
        [
            (
                24,  # cad_id
                1,  # schedule_ordinal
                "MANUFACTURER",  # exporter_status
                None,  # brand_name_holder
                "ON_SALE",  # product_eligibility
                "no",  # goods_placed_on_uk_market
                "yes",  # goods_export_only
                "no",  # any_raw_materials
                None,  # final_product_end_use
                1,  # country_of_manufacture_id
                1,  # accordance_with_standards
                0,  # is_repsonsible_person
                "Manufacturer",  # manufacturer_name
                "MANUAL",  # manufacturer_address_type
                2,  # created_by_id
                xd.cfs_product,  # product_xml
                None,  # legislation_xml
            ),
            (
                25,  # cad_id
                1,  # schedule_ordinal
                "NOT_MANUFACTURER",  # exporter_status
                "yes",  # brand_name_holder
                "MAY_BE_SOLD",  # product_eligibility
                "yes",  # goods_placed_on_uk_market
                "no",  # goods_export_only
                "yes",  # any_raw_materials
                "A product",  # final_product_end_use
                1,  # country_of_manufacture_id
                0,  # accordance_with_standards
                1,  # is_repsonsible_person
                None,  # manufacturer_name
                "MANUAL",  # manufacturer_address_type
                2,  # created_by_id
                None,  # product_xml
                xd.cfs_legislation,  # legislation_xml
            ),
            (
                25,  # cad_id
                2,  # schedule_ordinal
                "MANUFACTURER",  # exporter_status
                "no",  # brand_name_holder
                "ON_SALE",  # product_eligibility
                "no",  # goods_placed_on_uk_market
                "yes",  # goods_export_only
                "no",  # any_raw_materials
                None,  # final_product_end_use
                1,  # country_of_manufacture_id
                1,  # accordance_with_standards
                0,  # is_repsonsible_person
                "Manufacturer",  # manufacturer_name
                "MANUAL",  # manufacturer_address_type
                2,  # created_by_id
                xd.cfs_product_biocide,  # product_xml
                xd.cfs_legislation_biocide,  # legislation_xml
            ),
        ],
    ),
    export_application.export_certificate: (
        [("ca_id",), ("cad_id",), ("case_completion_datetime",), ("status",), ("case_reference",)],
        [
            (8, 18, datetime(2022, 4, 29), "DR", "CA/2022/9902"),
            (9, 10, datetime(2022, 4, 29), "AR", "CA/2022/9903"),
            (9, 19, datetime(2022, 4, 29), "AC", "CA/2022/9903/1"),
            (11, 21, datetime(2022, 4, 29), "DR", "CA/2022/9905"),
            (12, 22, datetime(2022, 4, 29), "AC", "CA/2022/9906"),
            (14, 24, datetime(2022, 4, 29), "DR", "CA/2022/9908"),
            (15, 11, datetime(2022, 4, 29), "AR", "CA/2022/9909"),
            (15, 12, datetime(2022, 4, 29), "AR", "CA/2022/9909/1"),
            (15, 25, datetime(2022, 4, 29), "AC", "CA/2022/9909/2"),
        ],
    ),
    export_application.export_certificate_docs: (
        [
            ("cad_id",),
            ("certificate_id",),
            ("document_legacy_id",),
            ("reference",),
            ("case_document_ref_id",),
            ("document_type",),
            ("country_id",),
            ("filename",),
            ("content_type",),
            ("file_size",),
            ("path",),
            ("created_datetime",),
            ("created_by_id",),
        ],
        [
            (
                18,  # cad_id
                1,  # certificate_id
                101,  # document_legacy_id
                "GMP/2022/00001",  # reference
                "GMP/2022/00001",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "gmp-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-1.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                18,  # cad_id
                2,  # certificate_id
                102,  # document_legacy_id
                "GMP/2022/00002",  # reference
                "GMP/2022/00002",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                2,  # country_id
                "gmp-cert-2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-2.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                18,  # cad_id
                3,  # certificate_id
                103,  # document_legacy_id
                "GMP/2022/00003",  # reference
                "GMP/2022/00003",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                3,  # country_id
                "gmp-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-3.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                19,  # cad_id
                4,  # certificate_id
                104,  # document_legacy_id
                "GMP/2022/00004",  # reference
                "GMP/2022/00004",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "gmp-cert-4.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/gmp-cert-4.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                21,  # cad_id
                5,  # certificate_id
                105,  # document_legacy_id
                "COM/2022/00001",  # reference
                "COM/2022/00001",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "com-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/com-cert-1.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                22,  # cad_id
                6,  # certificate_id
                106,  # document_legacy_id
                "COM/2022/00002",  # reference
                "COM/2022/00002",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "com-cert-2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/com-cert-2.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                24,  # cad_id
                7,  # certificate_id
                107,  # document_legacy_id
                "CFS/2022/00001",  # reference
                "CFS/2022/00001",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "cfs-cert-1.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/cfs-cert-1.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
            (
                25,  # cad_id
                8,  # certificate_id
                108,  # document_legacy_id
                "CFS/2022/00002",  # reference
                "CFS/2022/00002",  # case_document_ref_id
                "CERTIFICATE",  # documnet_type
                1,  # country_id
                "cfs-cert-2.pdf",  # filename
                "pdf",  # content_type
                100,  # file_size
                "path/to/cfs-cert-2.pdf",  # path
                datetime.now(),  # created_datetime
                2,  # created_by_id
            ),
        ],
    ),
    export_application.export_variations: (
        [
            ("ca_id",),
            ("is_active",),
            ("case_reference",),
            ("status",),
            ("requested_datetime",),
            ("requested_by_id",),
            ("what_varied",),
            ("closed_datetime",),
            ("closed_by_id",),
        ],
        [
            (
                9,  # ca_id
                0,  # is_active
                "CA/2022/9903/1",  # case_reference
                "CLOSED",  # status
                datetime.now(),  # requested_datetime
                2,  # requested_by_id
                "Make changes",  # what_varied
                datetime.now(),  # closed_datetime
                2,  # closed_by_id
            ),
            (
                15,  # ca_id
                0,  # is_active
                "CA/2022/9909/1",  # case_reference
                "CLOSED",  # status
                datetime.now(),  # requested_datetime
                2,  # requested_by_id
                "First changes",  # what_varied
                datetime.now(),  # closed_datetime
                2,  # closed_by_id
            ),
            (
                15,  # ca_id
                1,  # is_active
                "CA/2022/9909/2",  # case_reference
                "OPEN",  # status
                datetime.now(),  # requested_datetime
                2,  # requested_by_id
                "Second changes",  # what_varied
                datetime.now(),  # closed_datetime
                2,  # closed_by_id
            ),
        ],
    ),
}


class MockCursor:
    def __init__(self, *args, **kwargs):
        self.fetched = False
        self.rows = None
        self.data = None
        self.description = None

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args):
        pass

    def cursor(self):
        return self

    def execute(self, query):
        self.description, self.data = query_result.get(query, (None, None))

    @staticmethod
    def close():
        return

    def fetchmany(self, *args):
        if not self.fetched:
            self.rows = self.fetch_rows()
            self.fetched = True

        return next(self.rows)

    def fetch_rows(self):
        yield self.data

        self.fetched = False
        yield None


class MockConnect:
    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args):
        pass

    @staticmethod
    def cursor():
        return MockCursor()


def create_test_dm_models():
    web.User.objects.create(id=2, username="test_user")

    dm.Country.objects.bulk_create(
        [
            dm.Country(
                **dict(zip(["id", "name", "is_active", "type", "commission_code", "hmrc_code"], c))
            )
            for c in [
                (100, "CA", 1, "A", 100, "CA"),
                (101, "CB", 1, "A", 101, "CB"),
                (102, "CC", 1, "B", 102, "CC"),
                (103, "CD", 0, "A", 103, "CD"),
            ]
        ]
    )

    dm.CountryGroup.objects.bulk_create(
        [
            dm.CountryGroup(**dict(zip(["id", "country_group_id", "name", "comments"], cg)))
            for cg in [
                (200, "A", "TEST GROUP A", None),
                (201, "B", "TEST GROUP B", "Comment B"),
                (202, "C", "TEST GROUP C", "Comment C"),
            ]
        ]
    )

    dm.CountryGroupCountry.objects.bulk_create(
        [
            dm.CountryGroupCountry(**dict(zip(["countrygroup_id", "country_id"], cg)))
            for cg in [
                (200, 100),
                (200, 101),
                (201, 101),
                (201, 102),
                (201, 103),
            ]
        ]
    )

    dm.Unit.objects.bulk_create(
        [
            dm.Unit(**dict(zip(["unit_type", "description", "short_description", "hmrc_code"], u)))
            for u in [
                ("GS", "grams", "gs", 100),
                ("KGS", "kilos", "Kgs", 101),
                ("TBS", "terrabytes", "Tbs", 102),
            ]
        ]
    )

    dm.Constabulary.objects.bulk_create(
        [
            dm.Constabulary(**dict(zip(["is_active", "name", "region", "email"], c)))
            for c in [
                (1, "A", "A", "a@example.com"),  # /PS-IGNORE
                (1, "B", "B", "b@example.com"),  # /PS-IGNORE
                (1, "C", "C", "c@example.com"),  # /PS-IGNORE
            ]
        ]
    )

    dm.ObsoleteCalibreGroup.objects.bulk_create(
        [
            dm.ObsoleteCalibreGroup(**dict(zip(["legacy_id", "name", "is_active", "order"], ocg)))
            for ocg in [
                (1, "A", 1, 1),
                (2, "B", 1, 2),
                (3, "C", 1, 3),
            ]
        ]
    )
