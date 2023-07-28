import argparse
from typing import TYPE_CHECKING

import oracledb

from data_migration import models

from ._base import MigrationBaseCommand
from .config.run_order import DATA_TYPE, DATA_TYPE_QUERY_MODEL
from .utils.db import CONNECTION_CONFIG, new_process_pk
from .utils.format import format_name, format_row

if TYPE_CHECKING:
    from django.db.models import Model


class Command(MigrationBaseCommand):
    help = (
        """Connects to the V1 replica database and exports the data to the data_migration schema"""
    )

    DATA_TYPE_START = {
        "user": ["u", "user"],
        "reference": ["r", "ref", "reference"],
        "file": ["f", "file"],
        "import_application": ["ia", "import_application"],
        "export_application": ["ea", "export_application"],
    }

    def add_arguments(self, parser: argparse.ArgumentParser):
        super().add_arguments(parser)

        parser.add_argument(
            "--skip_post",
            help="Skip post export tasks",
            action="store_true",
        )

    def handle(self, *args, **options):
        super().handle(*args, **options)

        with oracledb.connect(**CONNECTION_CONFIG) as connection:
            self._export_data("user", connection, options["skip_user"])
            self._export_data("reference", connection, options["skip_ref"])
            self._export_data("file_folder", connection, options["skip_file"])
            self._export_data("import_application", connection, options["skip_ia"])
            self._export_data("export_application", connection, options["skip_export"])
            self._export_data("file", connection, options["skip_file"])
            self._post_export_tasks(options["skip_post"])

        self._log_script_end()

    def _export_data(
        self, data_type: DATA_TYPE, connection: oracledb.Connection, skip: bool
    ) -> None:
        """Retrives data from V1 and creates the objects in the data_migration models

        :param data_type: The type of data being exported
        :param connection: The connection to the V1 replica db
        :param batchsize: The number of records handled per batch
        :param skip: Skips the export of the current data_type
        """
        if not self._get_start_type(data_type):
            return

        query_models = DATA_TYPE_QUERY_MODEL[data_type]
        start, query_models = self._get_data_list(query_models)

        name = format_name(data_type)

        if skip:
            self.stdout.write(f"Skipping {name} Data Export")
            return

        self.stdout.write(f"Exporting {name} Data...")

        for idx, query_model in enumerate(query_models, start=start):
            self.stdout.write(
                f"\t{idx} - Exporting {query_model.query_name} to {query_model.model.__name__} model"
            )

            # Create a new cursor for each query
            # oracledb sometimes throws `IndexError: list index out of range` when reusing cursor
            with connection.cursor() as cursor:
                cursor.execute(query_model.query, query_model.parameters)
                columns = [col[0].lower() for col in cursor.description]

                while True:
                    rows = cursor.fetchmany(self.batch_size)
                    if not rows:
                        break

                    self._export_model_data(columns, rows, query_model.model)

            self._log_time()

        self.stdout.write(f"{name} Data Export Complete!")

    def _export_model_data(
        self, columns: list[str], rows: list[list[str]], base_model: "Model"
    ) -> None:
        """Handles the export of data to all the models populated by the data returned in the V1 query

        :param columns: The columns returned from the query
        :param rows: The rows of data returned from the query
        :param model: The model being targeted for creation
        """
        process_pk_start: int | None = new_process_pk() if base_model.PROCESS_PK else None

        for name in base_model.models_to_populate():
            model = getattr(models, name)
            fields = model.fields()
            batch = []

            for i, row in enumerate(rows):
                process_pk = process_pk_start + i if process_pk_start else None
                model_data = format_row(columns, row, fields, pk=process_pk)

                if model_data:
                    batch.append(model(**model_data))

            model.objects.bulk_create(batch)

    def _post_export_tasks(self, skip: bool) -> None:
        """Data fixes after export"""

        if skip:
            self.stdout.write("Skipping Post Export Tasks")
            return

        models.ImportApplication.objects.filter(last_updated_by_id__isnull=True).update(
            last_updated_by_id=0
        )

        self._log_time()
