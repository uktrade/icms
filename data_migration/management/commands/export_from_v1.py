import argparse
from typing import Any

import cx_Oracle
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from data_migration.queries import ref_query_model


class Command(BaseCommand):
    help = (
        """Connects to the V1 replica database and exports the data to the data_migration schema"""
    )

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--batchsize",
            help="Number of results per query batch",
            default=1000,
            type=int,
        )

    def handle(self, *args, **options):
        if not settings.ALLOW_DATA_MIGRATION or not settings.APP_ENV == "production":
            raise CommandError("Data migration has not been enabled for this environment")

        batchsize = options["batchsize"]

        connection_config = {
            "user": settings.ICMS_V1_REPLICA_USER,
            "password": settings.ICMS_V1_REPLICA_PASSWORD,
            "dsn": settings.ICMS_V1_REPLICA_DSN,
        }

        with cx_Oracle.connect(**connection_config) as connection:
            cursor = connection.cursor()
            self._export_reference_data(cursor, batchsize)
            cursor.close()

    def _format_data(self, column: str, data: Any) -> tuple[str, Any]:
        if column.endswith("_datetime") and data:
            # TODO: Check timezone how timezones work in django.
            # Assumption that source is UTC and datetime is passed to models with source tz
            data = timezone.utc.localize(data)

        return (column, data)

    def _format_row(self, columns: list[str], row: list[Any]) -> dict[str, Any]:
        return dict(self._format_data(columns[i], data) for i, data in enumerate(row))

    def _export_reference_data(self, cursor: cx_Oracle.Cursor, batchsize: int) -> None:
        self.stdout.write("Exporting Reference Data...")

        for query_model in ref_query_model:
            self.stdout.write(f"Exporting to {query_model.model.__name__} model")
            cursor.execute(query_model.query)
            columns = [col[0].lower() for col in cursor.description]

            while True:
                rows = cursor.fetchmany(batchsize)
                if not rows:
                    break

                query_model.model.objects.bulk_create(
                    [query_model.model(**self._format_row(columns, row)) for row in rows]
                )

        self.stdout.write("Reference Data Export Complete!")
