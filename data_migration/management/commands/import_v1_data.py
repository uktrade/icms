import argparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from data_migration.queries import ref_m2m, ref_source_target


class Command(BaseCommand):
    help = """Import the V1 data from the data migration models"""

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--batchsize",
            help="Number of results per query batch",
            default=1000,
            type=int,
        )

    def handle(self, *args, **options):
        if not settings.ALLOW_DATA_MIGRATION or not settings.APP_ENV == "production":
            raise CommandError("Data migration has not been enabled for this environment")

        batch_size = options["batchsize"]
        self._import_reference_data(batch_size)

    def _import_reference_data(self, batch_size):
        self.stdout.write("Importing Reference Data...")
        for st in ref_source_target:
            self.stdout.write(f"Importing {st.target.__name__} from {st.source.__name__}")
            st.target.objects.bulk_create(
                # TODO: Rewrite with islice
                # TODO: Consider get_source_data() method
                [st.target(**obj.data_export()) for obj in st.source.objects.all()],
                batch_size=batch_size,
            )

        self.stdout.write("Importing M2M relationships")
        for m2m in ref_m2m:
            self.stdout.write(
                f"Importing {m2m.target.__name__}_{m2m.field} from {m2m.source.__name__}"
            )
            through_table = getattr(m2m.target, m2m.field).through
            through_table.objects.bulk_create(
                # TODO: Rewrite with islice
                # TODO: Consider get_source_data() method
                [through_table(**obj.data_export()) for obj in m2m.source.objects.all()],
                batch_size=batch_size,
            )
