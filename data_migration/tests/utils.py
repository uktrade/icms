from datetime import datetime

from data_migration import models as dm
from data_migration.queries import files, import_application, reference, user
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
]


query_result = {
    reference.country: (
        [("id",), ("name",), ("status",), ("type",), ("commission_code",), ("hmrc_code",)],
        [
            (1, "CA", "ACTIVE", "A", 100, "CA"),
            (2, "CB", "ACTIVE", "A", 101, "CB"),
            (3, "CC", "ACTIVE", "B", 102, "CC"),
            (4, "CD", "INACTIVE", "A", 103, "CD"),
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
    user.offices: (
        [
            ("id",),
            ("importer_id",),
            ("legacy_id",),
            ("is_active",),
            ("postcode",),
            ("address",),
            ("eori_number",),
            ("address_entry_type",),
        ],
        [
            (1, 2, "2-1", 1, "ABC", "123 Test\nTest City", "GB123456789015", "SEARCH"),
            (2, 2, "2-2", 1, "DEF", "456 Test", "GB123456789016", "MANUAL"),
            (3, 3, "3-1", 1, "TEST", "ABC Test\nTest Town\nTest City", "GB123456789017", "MANUAL"),
        ],
    ),
    import_application.fa_authority_linked_offices: (
        [("firearmsauthority_id",), ("office_legacy_id",)],
        [(1, "2-1"), (1, "2-2"), (2, "3-1")],
    ),
    import_application.section5_linked_offices: (
        [("section5authority_id",), ("office_legacy_id",)],
        [(1, "2-1"), (1, "2-2"), (2, "3-1")],
    ),
    import_application.ia_licence: (
        [
            ("imad_id",),
            ("licence_start_date",),
            ("licence_end_date",),
            ("case_reference",),
            ("is_paper_only",),
            ("legacy_id",),
            ("status",),
        ],
        [
            (
                11,  # imad_id
                datetime(2022, 4, 27).date(),  # licence_start_date
                datetime(2023, 4, 27).date(),  # licence_end_date
                "IMA/2022/1234",  # case_reference
                0,  # is_paper_only
                1,  # legacy_id
                "AC",
            ),
            (
                12,
                datetime(2022, 4, 27).date(),
                datetime(2023, 4, 27).date(),
                "IMA/2022/2345",
                0,
                2,
                "AC",
            ),
        ],
    ),
    import_application.ia_licence_docs: (
        [
            ("reference",),
            ("content_type_id",),
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
                32,  # content_type_id
                1,  # licence_id
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
                "1235B",
                32,  # content_type_id
                2,
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
                32,  # content_type_id
                2,
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
                "2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "SILApplication",  # process_type
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
                "2-1",  # importer_office_legacy_id
                2,  # contact_id
                1,  # application_type
                "SILApplication",  # process_type
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
            ("status",),
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
                "ACTIVE",  # status
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
                **dict(zip(["id", "name", "status", "type", "commission_code", "hmrc_code"], c))
            )
            for c in [
                (100, "CA", "ACTIVE", "A", 100, "CA"),
                (101, "CB", "ACTIVE", "A", 101, "CB"),
                (102, "CC", "ACTIVE", "B", 102, "CC"),
                (103, "CD", "INACTIVE", "A", 103, "CD"),
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
