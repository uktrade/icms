import argparse
from itertools import islice

from django.core.management.base import BaseCommand

from data_migration.queries import DATA_TYPE, DATA_TYPE_XML

from .utils.format import format_name


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
            "--skip_ia",
            help="Skip import application data export",
            action="store_true",
        )

    def handle(self, *args, **options):
        self.batchsize = options["batchsize"]
        self._extract_xml_data("import_application", options["skip_ia"])

    def _extract_xml_data(self, data_type: DATA_TYPE, skip: bool) -> None:
        """Iterates over the models listed for the specified data_type and parses the xml from their parent"""

        parser_list = DATA_TYPE_XML[data_type]
        name = format_name(data_type)

        if skip:
            self.stdout.write(f"Skipping {name} Data Export")
            return

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
