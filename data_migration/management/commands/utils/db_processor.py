from collections.abc import Iterator
from contextlib import contextmanager

import oracledb

from data_migration.management.commands.utils.db import CONNECTION_CONFIG
from data_migration.queries.files_v1 import QUERY_LIST


class OracleDBProcessor:
    QUERIES: list[dict] = QUERY_LIST

    def __init__(self, limit: int, selected_queries: list[str], number_of_rows: int):
        self.limit = limit
        self.selected_queries = selected_queries
        self.number_of_rows = number_of_rows

    def get_query_list(self) -> Iterator[dict]:
        for query in self.QUERIES:
            if not self.selected_queries or (query["query_name"] in self.selected_queries):
                yield query

    def add_select_to_sql(self, sql: str) -> str:
        return f"WITH DOC_QUERY AS ({sql}) SELECT * FROM DOC_QUERY"

    def add_count_to_sql(self, sql: str) -> str:
        return f"WITH DOC_QUERY AS ({sql}) SELECT count(1) FROM DOC_QUERY"

    def add_limit_to_sql(self, sql: str) -> str:
        if not self.limit:
            return sql
        return f"{sql} FETCH FIRST {self.limit} ROWS ONLY"

    def get_basic_sql(self, query_dict: dict[str, str], start_from_datetime: str) -> str:
        return query_dict["query"].format(created_datetime_from=start_from_datetime)

    def get_count_sql(self, query_dict: dict[str, str], start_from_datetime: str) -> str:
        sql = self.get_basic_sql(query_dict, start_from_datetime)
        return self.add_count_to_sql(sql)

    def get_sql(self, query_dict: dict[str, str], start_from_datetime: str) -> str:
        sql = self.get_basic_sql(query_dict, start_from_datetime)
        sql = self.add_limit_to_sql(sql)
        return self.add_select_to_sql(sql)

    def get_db_connection(self) -> oracledb.Connection:
        return oracledb.connect(**CONNECTION_CONFIG)

    @contextmanager
    def execute_query(self, sql: str) -> Iterator:
        with self.get_db_connection().cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0].upper() for col in cursor.description]
            cursor.rowfactory = lambda *args: dict(zip(columns, args))

            def _rows():
                while True:
                    rows = cursor.fetchmany(self.number_of_rows)
                    if not rows:
                        break
                    yield from rows

            yield _rows()

    def execute_count_query(self, query_dict: dict[str, str], start_from_datetime: str) -> int:
        sql = self.get_count_sql(query_dict, start_from_datetime)
        with self.get_db_connection().cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchone()[0]
