import argparse
from itertools import islice

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from data_migration.queries import DATA_TYPE, DATA_TYPE_M2M, DATA_TYPE_SOURCE_TARGET


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

    def handle(self, *args, **options):
        if not settings.ALLOW_DATA_MIGRATION or not settings.APP_ENV == "production":
            raise CommandError("Data migration has not been enabled for this environment")

        batch_size = options["batchsize"]

        self._import_data("reference", batch_size, options["skip_ref"])
        self._import_data("import_application", batch_size, options["skip_ia"])

    def _import_data(self, data_type: DATA_TYPE, batch_size: int, skip: bool) -> None:
        source_target_list = DATA_TYPE_SOURCE_TARGET[data_type]
        m2m_list = DATA_TYPE_M2M[data_type]

        # Form a more human readible name "foo_bar" -> "Foo Bar"
        name = " ".join(dt.capitalize() for dt in data_type.split("_"))

        if skip:
            self.stdout.write(f"Skipping {name} Data Import")
            return

        self.stdout.write(f"Importing {name} Data")

        for st in source_target_list:
            self.stdout.write(f"Importing {st.target.__name__} from {st.source.__name__}")
            objs = st.source.get_source_data()

            while True:
                batch = [
                    st.target(**st.source.data_export(obj)) for obj in islice(objs, batch_size)
                ]
                if not batch:
                    break

                st.target.objects.bulk_create(batch)

        self.stdout.write(f"Importing {name} M2M relationships")

        for m2m in m2m_list:
            self.stdout.write(
                f"Importing {m2m.target.__name__}_{m2m.field} from {m2m.source.__name__}"
            )
            through_table = getattr(m2m.target, m2m.field).through
            objs = m2m.source.get_source_data()

            while True:
                batch = [
                    through_table(**m2m.source.data_export(obj)) for obj in islice(objs, batch_size)
                ]
                if not batch:
                    break

                through_table.objects.bulk_create(batch)

        self.stdout.write(f"{name} Data Imported!")
