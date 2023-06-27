from django.test import TestCase

from data_migration.management.commands.utils.db_processor import OracleDBProcessor

TEST_QUERY = f"""
select file_contents as blob_data, path, created_by_id, created_datetime  from data_migration_document
where  created_datetime > '{{created_datetime_from}}'
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
        query_dict = {"query_name": "test_query", "query": TEST_QUERY}
        expected_sql = """WITH DOC_QUERY AS (
select file_contents as blob_data, path, created_by_id, created_datetime  from data_migration_document
where  created_datetime > '2023-01-01 01:00:00'
ORDER BY created_datetime
 FETCH FIRST 100 ROWS ONLY) SELECT * FROM DOC_QUERY"""

        result = self.db.get_sql(query_dict, CREATED_DATETIME_ALT)
        assert result == expected_sql

    def test_get_count_sql(self):
        query_dict = {"query_name": "test_query", "query": TEST_QUERY}
        expected_sql = """WITH DOC_QUERY AS (
select file_contents as blob_data, path, created_by_id, created_datetime  from data_migration_document
where  created_datetime > '2023-01-01 01:00:00'
ORDER BY created_datetime
) SELECT count(1) FROM DOC_QUERY"""

        result = self.db.get_count_sql(query_dict, CREATED_DATETIME_ALT)
        assert result == expected_sql

    def test_get_query_list(self):
        db = OracleDBProcessor(100, None, 1)
        result = [query_dict for query_dict in db.get_query_list()]
        assert len(result) == 6
        assert set(result[0].keys()) == {"query_name", "query"}

    def test_get_filtered_query_list(self):
        db = OracleDBProcessor(100, ["V1_QUERY_2", "V1_QUERY_5"], 1)
        result = [query_dict["query_name"] for query_dict in db.get_query_list()]
        assert set(result) == {"V1_QUERY_2", "V1_QUERY_5"}
