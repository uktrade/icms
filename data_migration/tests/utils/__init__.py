from data_migration import models as dm
from web import models as web

from . import xml_data  # NOQA
from .ea_data import ea_query_result
from .ia_data import ia_query_result
from .reference_data import ref_query_result
from .user_data import user_query_result

query_result = ia_query_result | ea_query_result | ref_query_result | user_query_result


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


def create_test_dm_task_models():
    pass
