import argparse
from itertools import islice

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from data_migration.queries import DATA_TYPE, DATA_TYPE_M2M, DATA_TYPE_SOURCE_TARGET

from .utils.db import bulk_create


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
            "--skip_user",
            help="Skip user data export",
            action="store_true",
        )

    def handle(self, *args, **options):
        if not settings.ALLOW_DATA_MIGRATION or not settings.APP_ENV == "production":
            raise CommandError("Data migration has not been enabled for this environment")

        self.batch_size = options["batchsize"]

        self._import_data("user", options["skip_user"])
        self._import_data("reference", options["skip_ref"])
        self._import_data("import_application", options["skip_ia"])

    def _import_data(self, data_type: DATA_TYPE, skip: bool) -> None:
        source_target_list = DATA_TYPE_SOURCE_TARGET[data_type]
        m2m_list = DATA_TYPE_M2M[data_type]

        # Form a more human readable name "foo_bar" -> "Foo Bar"
        name = " ".join(dt.capitalize() for dt in data_type.split("_"))

        if skip:
            self.stdout.write(f"Skipping {name} Data Import")
            return

        self.stdout.write(f"Importing {name} Data")

        for source, target in source_target_list:
            self.stdout.write(f"Importing {target.__name__} from {source.__name__}")
            objs = source.get_source_data()

            while True:
                batch = [target(**source.data_export(obj)) for obj in islice(objs, self.batch_size)]
                if not batch:
                    break

                bulk_create(target, batch)

        self.stdout.write(f"Importing {name} M2M relationships")

        for source, target, field in m2m_list:
            self.stdout.write(f"Importing {target.__name__}_{field} from {source.__name__}")
            through_table = getattr(target, field).through
            objs = source.get_source_data()

            while True:
                batch = [
                    through_table(**source.data_export(obj))
                    for obj in islice(objs, self.batch_size)
                ]
                if not batch:
                    break

                through_table.objects.bulk_create(batch)

        self.stdout.write(f"{name} Data Imported!")
