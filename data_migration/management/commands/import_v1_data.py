import argparse
from itertools import islice

from data_migration import models as dm
from data_migration.queries import (
    DATA_TYPE,
    DATA_TYPE_M2M,
    DATA_TYPE_SOURCE_TARGET,
    TASK_LIST,
)
from web import models as web

from ._base import MigrationBaseCommand
from .utils.db import bulk_create
from .utils.format import format_name


class Command(MigrationBaseCommand):
    help = """Import the V1 data from the data migration models"""

    DATA_TYPE_START = {
        "reference": ["r", "ref", "reference", "r-m2m", "ref-m2m", "reference-m2m"],
        "file": ["f", "file"],
        "import_application": ["ia", "import_application", "ia-m2m", "import_application-m2m"],
    }

    def add_arguments(self, parser: argparse.ArgumentParser):
        super().add_arguments(parser)

        parser.add_argument(
            "--skip_task",
            help="Skip the creation of tasks",
            action="store_true",
        )

    def handle(self, *args, **options):
        super().handle(*args, **options)

        self._import_data("user", options["skip_user"])
        self._import_data("reference", options["skip_ref"])
        self._import_data("file", options["skip_file"])
        self._import_data("import_application", options["skip_ia"])
        self._create_missing_ia_licences(options["skip_ia"])
        self._create_tasks(options["skip_task"])

    def _import_data(self, data_type: DATA_TYPE, skip: bool) -> None:
        start_m2m = self.start_type.endswith("m2m")

        if not self._get_start_type(data_type):
            return

        name = format_name(data_type)

        if skip:
            self.stdout.write(f"Skipping {name} Data Import")
            return

        if not start_m2m:
            self._import_model(data_type)

        if data_type != "file":
            self._import_m2m(data_type)

        self.stdout.write(f"{name} Data Imported!")

    def _import_model(self, data_type: DATA_TYPE) -> None:
        start, source_target_list = self._get_data_list(DATA_TYPE_SOURCE_TARGET[data_type])
        name = format_name(data_type)
        self.stdout.write(f"Importing {name} Data")

        for idx, (source, target) in enumerate(source_target_list, start=start):
            self.stdout.write(f"\t{idx} - Importing {target.__name__} from {source.__name__}")

            objs = source.get_source_data()

            while True:
                batch = [target(**source.data_export(obj)) for obj in islice(objs, self.batch_size)]
                if not batch:
                    break

                bulk_create(target, batch)

    def _import_m2m(self, data_type: DATA_TYPE) -> None:
        start, m2m_list = self._get_data_list(DATA_TYPE_M2M[data_type])
        name = format_name(data_type)
        self.stdout.write(f"Importing {name} M2M relationships")

        for idx, (source, target, field) in enumerate(m2m_list, start=start):
            self.stdout.write(
                f"\t{idx} - Importing {target.__name__}_{field} from {source.__name__}"
            )

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
            self.stdout.write(f"\tCreating {task.TASK_TYPE} tasks")

            web.Task.objects.bulk_create(task.task_batch(), batch_size=self.batch_size)

        self.stdout.write("Task Data Created!")

    def _create_missing_ia_licences(self, skip: bool) -> None:
        if skip:
            self.stdout.write("Skipping Creating Missing Import Application Licences")
            return

        ia_qs = dm.ImportApplication.objects.filter(
            submit_datetime__isnull=False, ima__licences__isnull=True
        )

        draft_statuses = ["VARIATION_REQUESTED", "PROCESSING", "SUBMITTED"]
        draft_pks = ia_qs.filter(status__in=draft_statuses).values_list("pk", flat=True).iterator()
        self.stdout.write("Creating Draft Import Application Licences")

        while True:
            batch = [
                web.ImportApplicationLicence(import_application_id=pk, status="DR")
                for pk in islice(draft_pks, self.batch_size)
            ]

            if not batch:
                break

            web.ImportApplicationLicence.objects.bulk_create(batch)

        archived_pks = (
            ia_qs.exclude(status__in=draft_statuses).values_list("pk", flat=True).iterator()
        )
        self.stdout.write("Creating Archived Import Application Licences")

        while True:
            batch = [
                web.ImportApplicationLicence(import_application_id=pk, status="AR")
                for pk in islice(archived_pks, self.batch_size)
            ]

            if not batch:
                break

            web.ImportApplicationLicence.objects.bulk_create(batch)

        self.stdout.write("Missing Import Application Licence Data Created!")
