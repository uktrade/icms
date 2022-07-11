from datetime import datetime

from data_migration import models as dm
from data_migration.queries import files, import_application, reference, user
from web import models as web

query_result = {
    reference.country: (
        [("name",), ("status",), ("type",), ("commission_code",), ("hmrc_code",)],
        [
            ("CA", "ACTIVE", "A", 100, "CA"),
            ("CB", "ACTIVE", "A", 101, "CB"),
            ("CC", "ACTIVE", "B", 102, "CC"),
            ("CD", "INACTIVE", "A", 103, "CD"),
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
            (1000, "N", "N/A", "true", "Y", "Y", "true", "true", "Y", "Y", "NA", "Y", "Y"),
            (1001, "Y", "N", "true", "Y", "Y", None, "false", "N", "N", "N", "N", "N"),
        ],
    ),
    files.sps_application_files: (
        [
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
        ],
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
