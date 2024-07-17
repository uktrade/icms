import argparse
from itertools import islice

from django.db import connection

from data_migration import models as dm
from web import models as web

from ._base import MigrationBaseCommand
from .config.run_order import (
    DATA_TYPE,
    DATA_TYPE_M2M,
    DATA_TYPE_SOURCE_TARGET,
    TASK_LIST,
    TIMESTAMP_UPDATES,
)
from .utils.db import bulk_create
from .utils.format import format_name


class Command(MigrationBaseCommand):
    help = """Import the V1 data from the data migration models"""

    DATA_TYPE_START = {
        "user": ["u", "user"],
        "reference": ["r", "ref", "reference", "r-m2m", "ref-m2m", "reference-m2m"],
        "file": ["f", "file", "f-m2m", "file-m2m"],
        "import_application": ["ia", "import_application", "ia-m2m", "import_application-m2m"],
        "export_application": ["ea", "export_application", "ea-m2m", "export_application-m2m"],
    }

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
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
        self._import_data("import_application", options["skip_ia"])
        self._import_data("export_application", options["skip_export"])
        self._import_data("file", options["skip_file"])
        self._create_missing_ia_licences(options["skip_ia"])
        self._create_missing_export_certificates(options["skip_export"])
        self._create_tasks(options["skip_task"])
        self._update_auto_timestamps()
        self._log_script_end()

    def _import_data(self, data_type: DATA_TYPE, skip: bool) -> None:
        start_m2m = self.start_type.endswith("m2m")

        if not self._get_start_type(data_type):
            return

        name = format_name(data_type)

        if skip:
            self.log(f"Skipping {name} Data Import")
            return

        if not start_m2m:
            self._import_model(data_type)

        self._import_m2m(data_type)

        self.log(f"{name} Data Imported!")

    def _import_model(self, data_type: DATA_TYPE) -> None:
        start, source_target_list = self._get_data_list(DATA_TYPE_SOURCE_TARGET[data_type])
        name = format_name(data_type)
        self.log(f"Importing {name} Data")

        for idx, (source, target) in enumerate(source_target_list, start=start):
            self.log(f"\t{idx} - Importing {target.__name__} from {source.__name__}")
            count = 0

            objs = source.get_source_data()

            while True:
                batch = [target(**source.data_export(obj)) for obj in islice(objs, self.batch_size)]
                if not batch:
                    break

                bulk_create(target, batch)
                count += len(batch)

            self._log_time(count=count)

    def _import_m2m(self, data_type: DATA_TYPE) -> None:
        start, m2m_list = self._get_data_list(DATA_TYPE_M2M[data_type])
        name = format_name(data_type)
        self.log(f"Importing {name} M2M relationships")

        for idx, (source, target, field) in enumerate(m2m_list, start=start):
            self.log(f"\t{idx} - Importing {target.__name__}_{field} from {source.__name__}")
            count = 0

            through_table = getattr(target, field).through
            objs = source.get_m2m_data(target)

            while True:
                batch = [
                    through_table(**source.m2m_export(obj)) for obj in islice(objs, self.batch_size)
                ]
                if not batch:
                    break

                bulk_create(through_table, batch)
                count += len(batch)

            self._log_time(count=count)

    def _create_tasks(self, skip: bool) -> None:
        if skip:
            self.log("Skipping Task Data Import")
            return

        self.log("Creating Task Data")

        for task in TASK_LIST:
            self.log(f"\tCreating {task.TASK_TYPE} tasks")

            web.Task.objects.bulk_create(task.task_batch(), batch_size=self.batch_size)
            self._log_time()

        self.log("Task Data Created!")

    def _create_missing_packs(
        self,
        app_model: type[dm.ImportApplication] | type[dm.ExportApplication],
        pack_model: type[web.ImportApplicationLicence] | type[web.ExportApplicationCertificate],
        filter_params: dict[str, bool],
    ) -> None:
        """Create missing document packs for V1 where licences / certificates have not been generated"""

        statuses = (
            ("Draft", ["VARIATION_REQUESTED", "PROCESSING", "SUBMITTED"], "DR"),
            ("Revoked", ["REVOKED"], "RE"),
            ("Archived", ["COMPLETED", "STOPPED", "WITHDRAWN"], "AR"),
        )

        match app_model:
            case dm.ImportApplication:
                application_field = "import_application_id"
            case dm.ExportApplication:
                application_field = "export_application_id"
            case _:
                raise ValueError("app_model must be ImportApplication or ExportApplication")

        for name, app_status, pack_status in statuses:
            self.log(f"Creating {name} {pack_model.__name__}")

            pks = (
                app_model.objects.filter(
                    submit_datetime__isnull=False, status__in=app_status, **filter_params
                )
                .values_list("pk", flat=True)
                .iterator(chunk_size=2000)
            )

            while True:
                batch = [
                    pack_model(status=pack_status, **{application_field: pk})
                    for pk in islice(pks, self.batch_size)
                ]

                if not batch:
                    break

                pack_model.objects.bulk_create(batch)

    def _create_missing_ia_licences(self, skip: bool) -> None:
        if skip:
            self.log("Skipping Creating Missing Import Application Licences")
            return

        app_model = dm.ImportApplication
        pack_model = web.ImportApplicationLicence

        self._create_missing_packs(app_model, pack_model, {"ima__licences__isnull": True})
        self.log("Missing Import Application Licence Data Created!")

    def _create_missing_export_certificates(self, skip: bool) -> None:
        if skip:
            self.log("Skipping Creating Missing Export Application Certificates")
            return

        app_model = dm.ExportApplication
        pack_model = web.ExportApplicationCertificate

        self._create_missing_packs(app_model, pack_model, {"ca__certificates__isnull": True})
        self.log("Missing Export Application Certificate Data Created!")

    def _update_auto_timestamps(self):
        """Updates the auto_now_add timestamp fields to match the source data"""

        with connection.cursor() as cursor:
            for query in TIMESTAMP_UPDATES:
                cursor.execute(query)
