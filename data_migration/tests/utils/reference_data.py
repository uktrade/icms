from datetime import datetime

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
        ],
    ),
    queries.country_group: (
        [("country_group_id",), ("name",), ("comments",)],
        [
            ("A", "TEST GROUP A", None),
            ("B", "TEST GROUP B", "Comment B"),
            ("C", "TEST GROUP C", "Comment C"),
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
            (1, 1, "AT", "AC", "AN", "AD", datetime(2022, 12, 31, 12, 30), None, "TYPE_A", "KGS"),
            (2, 1, "BT", "BC", "BN", "BD", datetime.now(), None, "TYPE_B", "KGS"),
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
                datetime.now(),
                None,
                None,
                "TEX",
                datetime(2022, 12, 31, 12, 30),
                None,
            ),
            (2, 1, 1001, "TYPE_A", datetime.now(), None, None, "TEX", datetime.now(), None),
            (3, 1, 1002, "TYPE_B", datetime.now(), None, None, None, datetime.now(), None),
            (4, 1, 1003, "TYPE_B", datetime.now(), None, None, None, datetime.now(), None),
            (5, 1, 1004, "TYPE_C", datetime.now(), None, None, None, datetime.now(), None),
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
            ("start_datetime",),
            ("end_datetime",),
            ("is_active",),
            ("template_name",),
            ("template_code",),
            ("template_type",),
            ("application_domain",),
            ("template_title",),
            ("template_content",),
        ],
        [
            (
                1,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "Endorsement 1",  # template_name
                None,  # template_code
                "ENDORSEMENT",  # template_type
                "IMA",  # application_domain
                "Endorsement 1",  # template_title
                "First Endorsement",  # template_content
            ),
            (
                2,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "Endorsement 2",  # template_name
                None,  # template_code
                "ENDORSEMENT",  # template_type
                "IMA",  # application_domain
                "Endorsement 2",  # template_title
                "Second Endorsement",  # template_content
            ),
            (
                3,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "Endorsement 3",  # template_name
                None,  # template_code
                "ENDORSEMENT",  # template_type
                "IMA",  # application_domain
                "Endorsement 3",  # template_title
                "Third Endorsement",  # template_content
            ),
            (
                4,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "Letter 1",  # template_name
                "COVER_LETTER_1",  # template_code
                "LETTER_TEMPLATE",  # template_type
                "IMA",  # application_domain
                None,  # template_title
                xd.letter_template,  # template_content
            ),
            (
                5,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "Email 1",  # template_name
                "EMAIL_1",  # template_code
                "EMAIL_TEMPLATE",  # template_type
                "IAR",  # application_domain
                None,  # template_title
                xd.email_template,  # template_content
            ),
            (
                6,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "CFS Schedule 1",  # template_name
                "CFS_SCHEDULE_ENGLISH",  # template_code
                "CFS_SCHEDULE",  # template_type
                "CA",  # application_domain
                None,  # template_title
                None,  # template_content
            ),
            (
                7,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "CFS Declaration Spanish",  # template_name
                None,  # template_code
                "CFS_DECLARATION_TRANSLATION",  # template_type
                "CA",  # application_domain
                None,  # template_title
                "Some translated text",  # template_content
            ),
            (
                8,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "Wood Affidavit",  # template_name
                "IMA_WD_DECLARATION",  # template_code
                "DECLARATION",  # template_type
                "IMA",  # application_domain
                "Affidavit",  # template_title
                "Declaration content",  # template_content
            ),
            (
                9,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "Prior Surveillance Declaration",  # template_name
                "IMA_SPS_DECLARATION",  # template_code
                "DECLARATION",  # template_type
                "IMA",  # application_domain
                "Declaration of Truth",  # template_title
                "Declaration content",  # template_content
            ),
            (
                10,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                1,  # is_active
                "General Declaration of Truth",  # template_name
                "IMA_GEN_DECLARATION",  # template_code
                "DECLARATION",  # template_type
                "IMA",  # application_domain
                "Declaration of Truth",  # template_title
                "Declaration content",  # template_content
            ),
            (
                11,  # id
                datetime.now(),  # start_datetime
                None,  # end_datetime
                0,  # is_active
                "OPT Declaration",  # template_name
                "IMA_OPT_DECLARATION",  # template_code
                "DECLARATION",  # template_type
                "IMA",  # application_domain
                "Declaration of Truth",  # template_title
                "Declaration content",  # template_content
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
            (6, 3, "Paragraph 3", "Content 3"),
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
