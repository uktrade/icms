import argparse
from typing import Any

import cx_Oracle
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from data_migration.queries import DATA_TYPE, DATA_TYPE_QUERY_MODEL


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
        parser.add_argument(
            "--skip_ref",
            help="Skip reference data export",
            action="store_true",
        )
        parser.add_argument(
            "--skip_ia",
            help="Skip import application data export",
            action="store_true",
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

            self._export_data("reference", cursor, batchsize, options["skip_ref"])
            self._export_data("import_application", cursor, batchsize, options["skip_ia"])

            cursor.close()

    def _format_data(self, column: str, data: Any) -> tuple[str, Any]:
        if column.endswith("_datetime") and data:
            # TODO: Check timezone how timezones work in django.
            # Assumption that source is UTC and datetime is passed to models with source tz
            data = timezone.utc.localize(data)

        return (column, data)

    def _format_row(self, columns: list[str], row: list[Any]) -> dict[str, Any]:
        return dict(self._format_data(columns[i], data) for i, data in enumerate(row))

    def _export_data(
        self, data_type: DATA_TYPE, cursor: cx_Oracle.Cursor, batchsize: int, skip: bool
    ) -> None:
        query_models = DATA_TYPE_QUERY_MODEL[data_type]

        # Form a more human readable name "foo_bar" -> "Foo Bar"
        name = " ".join(dt.capitalize() for dt in data_type.split("_"))

        if skip:
            self.stdout.write(f"Skipping {name} Data Export")
            return

        self.stdout.write(f"Exporting {name} Data...")

        for query_model in query_models:
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

        self.stdout.write(f"{name} Data Export Complete!")
