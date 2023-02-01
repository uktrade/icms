import oracledb
from django.core.management.base import BaseCommand

from ._data_counts import CHECK_DATA_COUNTS, CHECK_DATA_QUERIES
from ._types import ModelT, Params
from .utils.db import CONNECTION_CONFIG


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.passes = 0
        self.failures = 0
        self.run_counts()
        self.run_queries()
        self.stdout.write(f"TOTAL PASS: {self.passes} - TOTAL FAIL: {self.failures}")

    def get_actual(self, model: ModelT, filter_params: Params) -> int:
        if isinstance(model, list):
            return sum(m.objects.filter(**filter_params).count() for m in model)

        return model.objects.filter(**filter_params).count()

    def run_queries(self):
        with oracledb.connect(**CONNECTION_CONFIG) as connection:
            for check in CHECK_DATA_QUERIES:
                expected = self.run_query(connection, check.query, check.bind_vars)
                self._log_result(check.name, expected, check.model, check.filter_params)

    def run_query(self, connection: oracledb.Connection, query: str, bind_vars: Params) -> int:
        with connection.cursor() as cursor:
            result: tuple[int] = cursor.execute(query, bind_vars).fetchone()

        return result[0]

    def run_counts(self) -> None:
        for check in CHECK_DATA_COUNTS:
            self._log_result(*check)

    def _log_result(
        self, name: str, expected: int, model: ModelT, filter_params: Params, exact: bool = True
    ):
        actual = self.get_actual(model, filter_params)

        if exact:
            result = "PASS" if expected == actual else "FAIL"
        else:
            result = "PASS" if expected <= actual else "FAIL"

        self.stdout.write(f"\t{result} - {name} -  EXPECTED: {expected} - ACTUAL: {actual}")
        self._increment_counts(result == "PASS")

    def _increment_counts(self, result: bool) -> None:
        if result:
            self.passes += 1
        else:
            self.failures += 1
