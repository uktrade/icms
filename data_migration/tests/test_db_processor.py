from django.test import TestCase

from data_migration.management.commands._types import QueryModel
from data_migration.management.commands.utils.db_processor import OracleDBProcessor

TEST_QUERY = """
SELECT file_contents AS blob_data, path, created_by_id, created_datetime  from data_migration_document
WHERE created_datetime > TO_DATE(:created_datetime, 'YYYY-MM-DD HH24:MI:SS`')
ORDER BY created_datetime
"""  # noqa: F541

CREATED_DATETIME_ALT = "2023-01-01 01:00:00"


class TestOracleDBProcessor(TestCase):
    def setUp(self):
        self.db = OracleDBProcessor(100, ["test_query"], 1)

    def test_add_limit_to_sql(self):
        assert (
            self.db.add_limit_to_sql("select * from table")
            == "select * from table FETCH FIRST 100 ROWS ONLY"
        )

    def test_get_sql(self):
        query_model = QueryModel(
            TEST_QUERY, "test_query", None, {"created_datetime": CREATED_DATETIME_ALT}
        )

        expected_sql = """WITH DOC_QUERY AS (
SELECT file_contents AS blob_data, path, created_by_id, created_datetime  from data_migration_document
WHERE created_datetime > TO_DATE(:created_datetime, 'YYYY-MM-DD HH24:MI:SS`')
ORDER BY created_datetime
 FETCH FIRST 100 ROWS ONLY) SELECT * FROM DOC_QUERY"""

        result = self.db.get_sql(query_model)
        assert result == expected_sql

    def test_get_count_sql(self):
        query_model = QueryModel(
            TEST_QUERY, "test_query", None, {"created_datetime": CREATED_DATETIME_ALT}
        )
        expected_sql = """WITH DOC_QUERY AS (
SELECT file_contents AS blob_data, path, created_by_id, created_datetime  from data_migration_document
WHERE created_datetime > TO_DATE(:created_datetime, 'YYYY-MM-DD HH24:MI:SS`')
ORDER BY created_datetime
) SELECT count(1) as count, SUM(file_size) as file_size FROM DOC_QUERY"""

        result = self.db.get_count_sql(query_model)
        assert result == expected_sql

    def test_get_query_list(self):
        db = OracleDBProcessor(100, None, 1)
        result = [query_model for query_model in db.get_query_list()]
        assert len(result) == 17

    def test_get_filtered_query_list(self):
        db = OracleDBProcessor(100, ["gmp_files", "fir_files"], 1)
        result = [query_model.query_name for query_model in db.get_query_list()]
        assert set(result) == {"gmp_files", "fir_files"}
