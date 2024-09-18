import datetime as dt

from data_migration import queries

from . import xml_data as xd

ref_query_result = {
    queries.country: (
        [("id",), ("name",), ("is_active",), ("type",), ("commission_code",), ("hmrc_code",)],
        [
            (1, "CA", 1, "A", 100, "CA"),
            (2, "CB", 1, "A", 101, "CB"),
            (3, "CC", 1, "B", 102, "CC"),
            (4, "CD", 0, "A", 103, "CD"),
            (5, "Aruba", 1, "B", 104, "CE"),
            (6, "Liberia", 1, "C", 105, "CF"),
            (7, "Mali", 1, "C", 107, "CG"),
            (8, "Gambia", 1, "B", 109, "CH"),
            (9, "Cameroon", 1, "A", 110, "CI"),
        ],
    ),
    queries.country_group: (
        [("country_group_id",), ("name",), ("comments",)],
        [
            ("FA_SIL_COO", "Firearms and Ammunition (SIL) COOs", None),
            ("FA_SIL_COC", "Firearms and Ammunition (SIL) COCs", "Comment B"),
            ("FA_OIL_COO", "Firearms and Ammunition (OIL) COOs", "Comment C"),
        ],
    ),
    queries.unit: (
        [("unit_type",), ("description",), ("short_description",), ("hmrc_code",)],
        [
            ("GS", "grams", "gs", 100),
            ("KGS", "kilos", "Kgs", 101),
            ("TBS", "terrabytes", "Tbs", 102),
        ],
    ),
    queries.constabularies: (
        [("id",), ("is_active",), ("name",), ("region",), ("email",)],
        [
            (1, 1, "A", "A", "a@example.com"),  # /PS-IGNORE
            (2, 1, "B", "B", "b@example.com"),  # /PS-IGNORE
            (3, 1, "C", "C", "c@example.com"),  # /PS-IGNORE
        ],
    ),
    queries.commodity_type: (
        [("type_code",), ("com_type_title",)],
        [("TYPE_A", "Type A"), ("TYPE_B", "Type B"), ("TYPE_C", "Type C")],
    ),
    queries.commodity_group: (
        [
            ("id",),
            ("is_active",),
            ("group_type",),
            ("group_code",),
            ("group_name",),
            ("group_description",),
            ("start_datetime",),
            ("end_datetime",),
            ("commodity_type_id",),
            ("unit_id",),
        ],
        [
            (
                1,
                1,
                "AT",
                "AC",
                "AN",
                "AD",
                dt.datetime(2022, 12, 31, 12, 30),
                None,
                "TYPE_A",
                "KGS",
            ),
            (2, 1, "BT", "BC", "BN", "BD", dt.datetime.now(), None, "TYPE_B", "KGS"),
        ],
    ),
    queries.commodity: (
        [
            ("id",),
            ("is_active",),
            ("commodity_code",),
            ("commodity_type_id",),
            ("validity_start_date",),
            ("validity_end_date",),
            ("quantity_threshold",),
            ("sigl_product_type",),
            ("start_datetime",),
            ("end_datetime",),
        ],
        [
            (
                1,
                1,
                1000,
                "TYPE_A",
                dt.datetime.now(),
                None,
                None,
                "TEX",
                dt.datetime(2022, 12, 31, 12, 30),
                None,
            ),
            (2, 1, 1001, "TYPE_A", dt.datetime.now(), None, None, "TEX", dt.datetime.now(), None),
            (3, 1, 1002, "TYPE_B", dt.datetime.now(), None, None, None, dt.datetime.now(), None),
            (4, 1, 1003, "TYPE_B", dt.datetime.now(), None, None, None, dt.datetime.now(), None),
            (5, 1, 1004, "TYPE_C", dt.datetime.now(), None, None, None, dt.datetime.now(), None),
        ],
    ),
    queries.obsolete_calibre_group: (
        [("id",), ("legacy_id",), ("name",), ("is_active",), ("order",)],
        [(1, 1, "Test OC Group", 1, 1), (2, 2, "Another OC Group", 1, 2), (3, 123, "C", 1, 3)],
    ),
    queries.obsolete_calibre: (
        [("id",), ("legacy_id",), ("name",), ("is_active",), ("order",), ("calibre_group_id",)],
        [(1, 3, "Inactive Test OC", 0, 2, 2), (2, 444, "Test OC", 1, 1, 1)],
    ),
    queries.template: (
        [
            ("id",),
            ("is_active",),
            ("template_name",),
            ("template_code",),
            ("template_type",),
            ("application_domain",),
        ],
        [
            (
                1,  # id
                1,  # is_active
                "Endorsement 1",  # template_name
                None,  # template_code
                "ENDORSEMENT",  # template_type
                "IMA",  # application_domain
            ),
            (
                2,  # id
                1,  # is_active
                "Endorsement 2",  # template_name
                None,  # template_code
                "ENDORSEMENT",  # template_type
                "IMA",  # application_domain
            ),
            (
                3,  # id
                1,  # is_active
                "Endorsement 3",  # template_name
                None,  # template_code
                "ENDORSEMENT",  # template_type
                "IMA",  # application_domain
            ),
            (
                4,  # id
                1,  # is_active
                "Letter 1",  # template_name
                "COVER_LETTER_1",  # template_code
                "LETTER_TEMPLATE",  # template_type
                "IMA",  # application_domain
            ),
            (
                5,  # id
                1,  # is_active
                "Email 1",  # template_name
                "EMAIL_1",  # template_code
                "EMAIL_TEMPLATE",  # template_type
                "IAR",  # application_domain
            ),
            (
                6,  # id
                1,  # is_active
                "CFS Schedule 1",  # template_name
                "CFS_SCHEDULE_ENGLISH",  # template_code
                "CFS_SCHEDULE",  # template_type
                "CA",  # application_domain
            ),
            (
                7,  # id
                1,  # is_active
                "CFS Declaration Spanish",  # template_name
                None,  # template_code
                "CFS_DECLARATION_TRANSLATION",  # template_type
                "CA",  # application_domain
            ),
            (
                8,  # id
                1,  # is_active
                "Wood Affidavit",  # template_name
                "IMA_WD_DECLARATION",  # template_code
                "DECLARATION",  # template_type
                "IMA",  # application_domain
            ),
            (
                9,  # id
                1,  # is_active
                "Prior Surveillance Declaration",  # template_name
                "IMA_SPS_DECLARATION",  # template_code
                "DECLARATION",  # template_type
                "IMA",  # application_domain
            ),
            (
                10,  # id
                1,  # is_active
                "General Declaration of Truth",  # template_name
                "IMA_GEN_DECLARATION",  # template_code
                "DECLARATION",  # template_type
                "IMA",  # application_domain
            ),
            (
                11,  # id
                0,  # is_active
                "OPT Declaration",  # template_name
                "IMA_OPT_DECLARATION",  # template_code
                "DECLARATION",  # template_type
                "IMA",  # application_domain
            ),
        ],
    ),
    queries.template_version: (
        [
            ("template_id",),
            ("start_datetime",),
            ("end_datetime",),
            ("is_active",),
            ("template_type",),
            ("title",),
            ("content",),
            ("version_number",),
            ("created_by_id",),
        ],
        [
            (
                1,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "ENDORSEMENT",  # template_type
                "Endorsement 1",  # title
                "First Endorsement",  # content
                1,  # version_number
                2,  # created_by_id
            ),
            (
                2,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "ENDORSEMENT",  # template_type
                "Endorsement 2",  # title
                "Second Endorsement",  # content
                1,  # version_number
                2,  # created_by_id
            ),
            (
                3,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "ENDORSEMENT",  # template_type
                "Endorsement 3",  # title
                "Third Endorsement",  # content
                1,  # version_number
                2,  # created_by_id
            ),
            (
                4,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "LETTER_TEMPLATE",  # template_type
                None,  # title
                xd.letter_template,  # content
                1,  # version_number
                2,  # created_by_id
            ),
            (
                5,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "EMAIL_TEMPLATE",  # template_type
                "Email Subject",  # title
                xd.email_template,  # content
                1,  # version_number
                2,  # created_by_id
            ),
            (
                6,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "CFS_SCHEDULE",  # template_type
                None,  # title
                None,  # content
                1,  # version_number
                2,  # created_by_id
            ),
            (
                7,  # template_id
                dt.datetime(2020, 1, 12, 7, 30),  # start_datetime
                dt.datetime.now(),  # end_datetime
                0,  # is_active
                "CFS_DECLARATION_TRANSLATION",  # template_type
                None,  # title
                "Some translated text",  # content
                1,  # version_number
                2,  # created_by_id
            ),
            (
                7,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "CFS_DECLARATION_TRANSLATION",  # template_type
                None,  # title
                "Some translated text with &apos; data &apos;",  # content
                2,  # version_number
                2,  # created_by_id
            ),
            (
                8,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "DECLARATION",  # template_type
                "Affidavit",  # title
                "Declaration content",  # content
                1,  # version_number
                2,  # created_by_id
            ),
            (
                9,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "DECLARATION",  # template_type
                "Declaration of Truth",  # title
                "Declaration content",  # content
                1,  # version_number
                2,  # created_by_id
            ),
            (
                10,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "DECLARATION",  # template_type
                "Declaration of Truth",  # title
                "Declaration content",  # content
                1,  # version_number
                2,  # created_by_id
            ),
            (
                11,  # template_id
                dt.datetime.now(),  # start_datetime
                None,  # end_datetime
                0,  # is_active
                "DECLARATION",  # template_type
                "Declaration of Truth",  # title
                "Declaration content",  # content
                1,  # version_number
                2,  # created_by_id
            ),
        ],
    ),
    queries.cfs_paragraph: (
        [
            ("template_id",),
            ("ordinal",),
            ("name",),
            ("content",),
        ],
        [
            (6, 1, "Paragraph 1", "Content 1"),
            (6, 2, "Paragraph 2", "Content 2"),
            (6, 3, "Paragraph 3", "Content &apos;3&apos;"),
        ],
    ),
    queries.template_country: (
        [("template_id",), ("country_id",)],
        [(7, 2), (7, 3)],
    ),
    queries.endorsement_template: (
        [("importapplicationtype_id",), ("template_id",)],
        [(1, 1), (5, 2), (5, 3), (6, 1), (6, 2), (6, 3)],
    ),
}
