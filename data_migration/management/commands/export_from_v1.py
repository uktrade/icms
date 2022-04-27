import argparse
from itertools import islice
from typing import TYPE_CHECKING, Optional

import cx_Oracle
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from data_migration import models
from data_migration.models.user import Importer, Office, User
from data_migration.queries import DATA_TYPE, DATA_TYPE_QUERY_MODEL, DATA_TYPE_XML

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

        self.batchsize = options["batchsize"]

        connection_config = {
            "user": settings.ICMS_V1_REPLICA_USER,
            "password": settings.ICMS_V1_REPLICA_PASSWORD,
            "dsn": settings.ICMS_V1_REPLICA_DSN,
        }

        if not options["skip_user"]:
            self._create_user_data()

        with cx_Oracle.connect(**connection_config) as connection:
            cursor = connection.cursor()

            self._export_data("reference", cursor, options["skip_ref"])
            self._export_data("import_application", cursor, options["skip_ia"])

            cursor.close()

    def _export_data(self, data_type: DATA_TYPE, cursor: cx_Oracle.Cursor, skip: bool) -> None:
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
                rows = cursor.fetchmany(self.batchsize)
                if not rows:
                    break

                self._export_model_data(columns, rows, model)

        self._extract_xml_data(data_type)

        self.stdout.write(f"{name} Data Export Complete!")

    def _export_model_data(
        self, columns: list[str], rows: list[list[str]], base_model: "Model"
    ) -> None:
        """Handles the export of data to all the models populated by the data returned in the V1 query

        :param columns: The columns returned from the query
        :param rows: The rows of data returned from the query
        :param model: The model being targeted for creation
        """
        process_pk: Optional[int] = new_process_pk() if base_model.PROCESS_PK else None

        for name in base_model.models_to_populate():
            model = getattr(models, name)
            fields = model.fields()

            if process_pk:
                model.objects.bulk_create(
                    [
                        model(**format_row(columns, row, fields, pk=process_pk + i))
                        for i, row in enumerate(rows)
                    ]
                )
            else:
                model.objects.bulk_create(
                    [model(**format_row(columns, row, fields)) for row in rows]
                )

    def _extract_xml_data(self, data_type: DATA_TYPE) -> None:
        """Iterates over the models listed for the specified data_type and parses the xml from their parent"""

        parser_list = DATA_TYPE_XML[data_type]
        name = format_name(data_type)

        self.stdout.write(f"Extracting xml data for {name}")

        for parser in parser_list:
            self.stdout.write(parser.log_message())
            objs = parser.get_queryset()

            while True:
                batch = list(islice(objs, self.batchsize))

                if not batch:
                    break

                for model, data in parser.parse_xml(batch).items():
                    model.objects.bulk_create(data)

        self.stdout.write("XML extraction complete")

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
