import argparse
from typing import TYPE_CHECKING

import cx_Oracle
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from data_migration.models import ImportApplication, Process
from data_migration.models.user import Importer, Office, User
from data_migration.queries import DATA_TYPE, DATA_TYPE_QUERY_MODEL

from .utils.db import new_process_pk
from .utils.format import format_name, format_row

if TYPE_CHECKING:
    from django.db.models import Model


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
        parser.add_argument(
            "--skip_user",
            help="Skip user data export",
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

        if not options["skip_user"]:
            self._create_user_data()

        with cx_Oracle.connect(**connection_config) as connection:
            cursor = connection.cursor()

            self._export_data("reference", cursor, batchsize, options["skip_ref"])
            self._export_data("import_application", cursor, batchsize, options["skip_ia"])

            cursor.close()

    def _export_data(
        self, data_type: DATA_TYPE, cursor: cx_Oracle.Cursor, batchsize: int, skip: bool
    ) -> None:
        """Retrives data from V1 and creates the objects in the data_migration models

        :param data_type: The type of data being exported
        :param cursor: The cursor for the connection to the V1
        :param batchsize: The number of records handled per batch
        :param skip: Skips the export of the current data_type
        """
        query_models = DATA_TYPE_QUERY_MODEL[data_type]
        name = format_name(data_type)

        if skip:
            self.stdout.write(f"Skipping {name} Data Export")
            return

        self.stdout.write(f"Exporting {name} Data...")

        for query, model in query_models:
            self.stdout.write(f"Exporting to {model.__name__} model")
            cursor.execute(query)
            columns = [col[0].lower() for col in cursor.description]

            while True:
                rows = cursor.fetchmany(batchsize)
                if not rows:
                    break

                if data_type == "import_application":
                    self._export_ia_data(columns, list(rows), model)
                else:
                    model.objects.bulk_create([model(**format_row(columns, row)) for row in rows])

        self.stdout.write(f"{name} Data Export Complete!")

    def _export_ia_data(self, columns: list[str], rows: list[list[str]], model: "Model") -> None:
        """Handles the creation of import application data in the data_migration models

        :param columns: The columns returned from the query
        :param rows: The rows of data returned from the query
        :param model: The model being targeted for creation
        """

        if model.__name__.endswith("Application"):
            # In V2 each application inherits from ImportApplication
            # ImportApplication inherit from Process
            # The pks much match the Process pk so we can't rely on autoincrement
            start_pk = new_process_pk()
            process_fields = Process.fields()
            Process.objects.bulk_create(
                [
                    Process(**format_row(columns, row, process_fields, pk=start_pk + i))
                    for i, row in enumerate(rows)
                ]
            )
            ia_fields = ImportApplication.fields()
            ImportApplication.objects.bulk_create(
                [
                    ImportApplication(**format_row(columns, row, ia_fields, pk=start_pk + i))
                    for i, row in enumerate(rows)
                ]
            )

            model_fields = model.fields()
            model.objects.bulk_create(
                [
                    model(**format_row(columns, row, model_fields, pk=start_pk + i))
                    for i, row in enumerate(rows)
                ]
            )
            # TODO: Create tasks for the application data
        else:
            model.objects.bulk_create([model(**format_row(columns, row)) for row in rows])

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

        Importer.objects.create(
            id=2,
            is_active=True,
            name="Prod org",
            registered_number="42",
            type="ORGANISATION",
        )

        Office.objects.create(
            id=2,
            is_active=True,
            postcode="SW1A 2HP",
            address="3 Whitehall Pl, Westminster, London",
        )
        self.stdout.write("User Data Created!")
