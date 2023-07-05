from collections.abc import Iterator
from contextlib import contextmanager

import oracledb

from data_migration.management.commands.config.run_order import (
    QueryModel,
    file_query_model,
)
from data_migration.management.commands.utils.db import CONNECTION_CONFIG


class OracleDBProcessor:
    QUERIES: list[QueryModel] = file_query_model

    def __init__(self, limit: int, selected_queries: list[str], number_of_rows: int):
        self.limit = limit
        self.selected_queries = selected_queries
        self.number_of_rows = number_of_rows

    def get_query_list(self) -> Iterator[QueryModel]:
        for query in self.QUERIES:
            if not self.selected_queries or (query.query_name in self.selected_queries):
                yield query

    def add_select_to_sql(self, sql: str) -> str:
        return f"WITH DOC_QUERY AS ({sql}) SELECT * FROM DOC_QUERY"

    def add_count_to_sql(self, sql: str) -> str:
        return f"WITH DOC_QUERY AS ({sql}) SELECT count(1) as count, SUM(file_size) as file_size FROM DOC_QUERY"

    def add_limit_to_sql(self, sql: str) -> str:
        if not self.limit:
            return sql
        return f"{sql} FETCH FIRST {self.limit} ROWS ONLY"

    def get_count_sql(self, query_model: QueryModel) -> str:
        return self.add_count_to_sql(query_model.query)

    def get_sql(self, query_model: QueryModel) -> str:
        sql = self.add_limit_to_sql(query_model.query)
        return self.add_select_to_sql(sql)

    def get_db_connection(self) -> oracledb.Connection:
        return oracledb.connect(**CONNECTION_CONFIG)

    @contextmanager
    def execute_query(self, sql: str, parameters: dict) -> Iterator:
        with self.get_db_connection().cursor() as cursor:
            cursor.execute(sql, parameters)
            columns = [col[0].upper() for col in cursor.description]
            cursor.rowfactory = lambda *args: dict(zip(columns, args))

            def _rows():
                while True:
                    rows = cursor.fetchmany(self.number_of_rows)
                    if not rows:
                        break
                    yield from rows

            yield _rows()

    def execute_count_query(self, query_model: QueryModel, parameters: dict) -> tuple[int, int]:
        sql = self.get_count_sql(query_model)
        return self.execute_cumulative_query(sql, parameters)

    def execute_cumulative_query(self, sql: str, parameters: dict) -> tuple[int, int]:
        with self.execute_query(sql, parameters) as rows:
            result = next(rows)
            return result["COUNT"] or 0, result["FILE_SIZE"] or 0


AVAILABLE_QUERIES: list[str] = [query.query_name for query in file_query_model]
