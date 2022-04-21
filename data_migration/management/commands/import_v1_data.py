import argparse
from itertools import islice

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from data_migration import models as dm
from data_migration.queries import (
    DATA_TYPE,
    DATA_TYPE_M2M,
    DATA_TYPE_SOURCE_TARGET,
    TASK_LIST,
)
from web import models as web

from .utils.db import bulk_create
from .utils.format import format_name


class Command(BaseCommand):
    help = """Import the V1 data from the data migration models"""

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--batchsize",
            help="Number of results per query batch",
            default=1000,
            type=int,
        )
        parser.add_argument(
            "--skip_ref",
            help="Skip reference data import",
            action="store_true",
        )
        parser.add_argument(
            "--skip_ia",
            help="Skip import application data import",
            action="store_true",
        )
        parser.add_argument(
            "--skip_task",
            help="Skip the creation of tasks",
            action="store_true",
        )
        parser.add_argument(
            "--skip_user",
            help="Skip user data import",
            action="store_true",
        )

    def handle(self, *args, **options):
        if not settings.ALLOW_DATA_MIGRATION or not settings.APP_ENV == "production":
            raise CommandError("Data migration has not been enabled for this environment")

        self.batch_size = options["batchsize"]

        self._import_data("user", options["skip_user"])
        self._import_data("reference", options["skip_ref"])
        self._import_data("import_application", options["skip_ia"])
        self._create_draft_ia_licences(options["skip_ia"])
        self._create_tasks(options["skip_task"])

    def _import_data(self, data_type: DATA_TYPE, skip: bool) -> None:
        name = format_name(data_type)

        if skip:
            self.stdout.write(f"Skipping {name} Data Import")
            return

        self._import_model(data_type)
        self._import_m2m(data_type)

        self.stdout.write(f"{name} Data Imported!")

    def _import_model(self, data_type: DATA_TYPE) -> None:
        source_target_list = DATA_TYPE_SOURCE_TARGET[data_type]
        name = format_name(data_type)

        self.stdout.write(f"Importing {name} Data")
        for source, target in source_target_list:
            self.stdout.write(f"Importing {target.__name__} from {source.__name__}")

            objs = source.get_source_data()

            while True:
                batch = [target(**source.data_export(obj)) for obj in islice(objs, self.batch_size)]
                if not batch:
                    break

                bulk_create(target, batch)

    def _import_m2m(self, data_type: DATA_TYPE) -> None:
        m2m_list = DATA_TYPE_M2M[data_type]
        name = format_name(data_type)
        self.stdout.write(f"Importing {name} M2M relationships")

        for source, target, field in m2m_list:
            self.stdout.write(f"Importing {target.__name__}_{field} from {source.__name__}")

            through_table = getattr(target, field).through
            objs = source.get_m2m_data(target)

            while True:
                batch = [
                    through_table(**source.m2m_export(obj)) for obj in islice(objs, self.batch_size)
                ]
                if not batch:
                    break

                bulk_create(through_table, batch)

    def _create_tasks(self, skip: bool) -> None:
        if skip:
            self.stdout.write("Skipping Task Data Import")
            return

        self.stdout.write("Creating Task Data")

        for task in TASK_LIST:
            self.stdout.write(f"Creating {task.TASK_TYPE} tasks")

            web.Task.objects.bulk_create(task.task_batch(), batch_size=self.batch_size)

        self.stdout.write("Task Data Created!")

    def _create_draft_ia_licences(self, skip: bool) -> None:
        if skip:
            self.stdout.write("Skipping Creating Draft Import Application Licences")
            return

        self.stdout.write("Creating Draft Import Application Licences")
        ia_pks = (
            dm.ImportApplication.objects.filter(licences__isnull=True)
            .values_list("pk", flat=True)
            .iterator()
        )

        while True:
            batch = [
                web.ImportApplicationLicence(import_application_id=pk, status="DR")
                for pk in islice(ia_pks, self.batch_size)
            ]

            if not batch:
                break

            web.ImportApplicationLicence.objects.bulk_create(batch)

        self.stdout.write("Draft Import Application Licence Data Created!")
