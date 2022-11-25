from itertools import islice
from typing import TYPE_CHECKING, Optional

import oracledb
from django.conf import settings
from django.core.management.base import CommandError

from data_migration import models
from data_migration.models.user import User
from data_migration.queries import DATA_TYPE, DATA_TYPE_QUERY_MODEL, FILE_MODELS

from ._base import MigrationBaseCommand
from .utils.db import new_process_pk
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

    def handle(self, *args, **options):
        super().handle(*args, **options)

        connection_config = {
            "user": settings.ICMS_V1_REPLICA_USER,
            "password": settings.ICMS_V1_REPLICA_PASSWORD,
            "dsn": settings.ICMS_V1_REPLICA_DSN,
        }

        if not options["skip_user"]:
            self._create_user_data()

        with oracledb.connect(**connection_config) as connection:
            with connection.cursor() as cursor:
                self._export_data("user", cursor, options["skip_user"])
                self._export_data("reference", cursor, options["skip_ref"])
                self._export_data("file", cursor, options["skip_file"])
                self._export_data("import_application", cursor, options["skip_ia"])
                self._export_data("export_application", cursor, options["skip_export"])

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

        for idx, (module, query_name, model) in enumerate(query_models, start=start):
            self.stdout.write(f"\t{idx} - Exporting {query_name} to {model.__name__} model")
            query = getattr(module, query_name)

            # Create a new cursor for each query
            # oracledb sometimes throws `IndexError: list index out of range` when reusing cursor
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0].lower() for col in cursor.description]

                while True:
                    rows = cursor.fetchmany(self.batch_size)
                    if not rows:
                        break

                    self._export_model_data(columns, rows, model)

            self._log_time()

        if data_type == "file":
            self._extract_file_data()

        self.stdout.write(f"{name} Data Export Complete!")

    def _export_model_data(
        self, columns: list[str], rows: list[list[str]], base_model: "Model"
    ) -> None:
        """Handles the export of data to all the models populated by the data returned in the V1 query

        :param columns: The columns returned from the query
        :param rows: The rows of data returned from the query
        :param model: The model being targeted for creation
        """
        process_pk_start: Optional[int] = new_process_pk() if base_model.PROCESS_PK else None

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

    def _extract_file_data(self) -> None:
        """Normalises file data as per V1 structure"""

        self.stdout.write("Extracting file data")

        for model in FILE_MODELS:
            self.stdout.write(f"\tExtracting {model.__name__}")
            data = model.get_from_combined()

            while True:
                batch = [model(**obj) for obj in islice(data, self.batch_size)]

                if not batch:
                    break

                model.objects.bulk_create(batch)

            self._log_time()

        self.stdout.write("File data extracted")

    def _create_user_data(self):
        """Creates dummy user data prior to users being migrated"""

        self.stdout.write("Creating User Data...")
        username = settings.ICMS_PROD_USER
        password = settings.ICMS_PROD_PASSWORD

        if not username or not password:
            raise CommandError("No user details found for this environment")

        if User.objects.exists():
            self.stdout.write("User data exists. Skipping.")
            return

        user = User.objects.create(
            id=2,
            username=username,
            first_name="Prod",
            last_name="User",
            email=username,
            is_active=True,
            title="Mr",
            password_disposition="FULL",
        )
        user.set_password(password)
        user.save()
        self._log_time()
        self.stdout.write("User Data Created!")
