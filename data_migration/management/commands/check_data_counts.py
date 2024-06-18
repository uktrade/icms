import argparse
from typing import Any

import oracledb
from django.core.management.base import BaseCommand

from data_migration.management.commands.types import CheckFileQuery, CheckQuery
from web.models import UniqueReference
from web.utils.s3 import get_s3_file_count, get_s3_resource

from .config.data_counts import (
    CHECK_DATA_COUNTS,
    CHECK_DATA_QUERIES,
    CHECK_FILE_COUNTS,
    CHECK_MODELS,
    UNIQUE_REFERENCES,
)
from .types import Anno, ModelT, Params, Val
from .utils.db import CONNECTION_CONFIG

DB_CHECKS = ["counts", "model_counts", "data_queries", "max_reference"]
FILE_CHECKS = ["s3_file_counts", "file_queries"]
CHECKS = DB_CHECKS + FILE_CHECKS


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--fail_only",
            help="Shows only the failures and not the passes",
            action="store_true",
        )
        parser.add_argument(
            "--checks",
            help="Specify which check to run by name or group alias (all/db/files), defaults to all available checks",
            nargs="+",
            choices=CHECKS + ["db", "files"],
            type=str,
            default="all",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        self.fail_only = options["fail_only"]
        self.passes = 0
        self.failures = 0
        checks = options["checks"]
        if "all" in checks:
            checks = CHECKS
        elif "db" in checks:
            checks = DB_CHECKS
        elif "files" in checks:
            checks = FILE_CHECKS
        if "counts" in checks:
            self.stdout.write("\nRunning count checks")
            self.run_counts()
        if "model_counts" in checks:
            self.stdout.write("\nRunning model count checks")
            self.run_model_counts()
        if "data_queries" in checks:
            self.stdout.write("\nRunning data queries checks")
            self.run_queries(CHECK_DATA_QUERIES)
        if "file_queries" in checks:
            self.stdout.write("\nRunning file db queries checks")
            self.run_queries(CHECK_FILE_COUNTS)
        if "max_reference" in checks:
            self.stdout.write("\nRunning max reference checks")
            self.check_max_licence_and_certificate_references()
        if "s3_file_counts" in checks:
            self.stdout.write("\nRunning s3 file count checks")
            self.run_file_counts()
        self.stdout.write(f"TOTAL PASS: {self.passes} - TOTAL FAIL: {self.failures}")

    def get_actual(
        self,
        model: ModelT,
        filter_params: Params,
        exclude_params: Params,
        annotation: Anno = None,
        values: Val = None,
    ) -> int:
        """Retrieve to actual counts for the models or list of models migrated to V2

        :param model: The model or list of models to be counted
        :param filter_params: A dict of filter conditions to be used when querying the model
        :param exclude_params: A dict of exclude conditions to be used when querying the model
        """
        if not annotation:
            annotation = {}

        if not values:
            values = []

        if isinstance(model, list):
            return sum(
                m.objects.annotate(**annotation)
                .filter(**filter_params)
                .exclude(**exclude_params)
                .count()
                for m in model
            )

        return (
            model.objects.values(*values)
            .annotate(**annotation)
            .filter(**filter_params)
            .exclude(**exclude_params)
            .count()
        )

    def run_file_counts(self) -> None:
        """Compares the file counts in V1 database to the amount of files uploaded to s3"""
        s3_resource = get_s3_resource()
        with oracledb.connect(**CONNECTION_CONFIG) as connection:
            for check in CHECK_FILE_COUNTS:
                expected = self.run_query(connection, check.query, check.bind_vars)
                actual = get_s3_file_count(s3_resource, check.get_path_prefixes())
                actual += check.adjustment  # Adjust to account for excluded data. See check.note
                self._log_result(check.name, expected, actual)

    def run_queries(self, queries: list[CheckQuery] | list[CheckFileQuery]) -> None:
        """Iterates over CHECK_DATA_QUERIES and CHECK_FILE_COUNTS and runs queries in V1 to retrieve the data counts prior to data migration"""

        with oracledb.connect(**CONNECTION_CONFIG) as connection:
            for check in queries:
                expected = self.run_query(connection, check.query, check.bind_vars)
                actual = self.get_actual(check.model, check.filter_params, check.exclude_params)
                actual += check.adjustment  # Adjust to account for excluded data. See check.note
                self._log_result(check.name, expected, actual)

    def run_query(self, connection: oracledb.Connection, query: str, bind_vars: Params) -> int:
        """Execute a specific query in V1 and return the result

        :param connection: The connection to the V1 oracle db
        :param query: The query to be run
        :param bind_vars: A dict of bind varaibles to be passed to the query
        """

        with connection.cursor() as cursor:
            result: tuple[int] = cursor.execute(query, bind_vars).fetchone()

        return result[0]

    def run_counts(self) -> None:
        """Iterates over CHECK_DATA_COUNTS to compare expected counts to actual counts in V2"""

        for check in CHECK_DATA_COUNTS:
            actual = self.get_actual(
                check.model,
                check.filter_params,
                check.exclude_params,
                annotation=check.annotation,
                values=check.values,
            )
            self._log_result(check.name, check.expected_count, actual)

    def run_model_counts(self) -> None:
        """Iterates over CHECK_MODELS to compare counts of model queires match"""

        for check in CHECK_MODELS:
            count_a = self.get_actual(
                check.model_a,
                check.filter_params_a,
                {},
            )
            count_b = self.get_actual(
                check.model_b,
                check.filter_params_b,
                {},
            )
            self._log_result(check.name, count_a, count_b)

    def check_max_licence_and_certificate_references(self) -> None:
        with oracledb.connect(**CONNECTION_CONFIG) as connection:
            for check in UNIQUE_REFERENCES:
                ref = (
                    UniqueReference.objects.filter(**check.filter_params)
                    .order_by("-year", "-reference")
                    .first()
                )

                result = self.run_query(connection, check.query, check.bind_vars)
                self._log_result(check.name, str(result), ref.reference)

    def _log_result(self, name: str, expected: int | str, actual: int | str) -> None:
        """Compares the expected values with the actual values and logs the result

        :param name: The name of the check to be logged
        :param expected: The expected count of the data
        :param actual: The actual count of the data
        """

        result = "PASS" if expected == actual else "FAIL"

        if not self.fail_only or result == "FAIL":
            self.stdout.write(
                f"\t{result} - {name} -  EXPECTED[V1]: {expected} - ACTUAL[V2]: {actual}"
            )

        self._increment_counts(result == "PASS")

    def _increment_counts(self, result: bool) -> None:
        """Increments the pass and fail counts based on result

        :param result: A boolean of the PASS / FAIL result
        """
        if result:
            self.passes += 1
        else:
            self.failures += 1
