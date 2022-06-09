import argparse
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from data_migration.queries import DATA_TYPE


class MigrationBaseCommand(BaseCommand):
    DATA_TYPE_START: dict[str, list[str]] = {}

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--batchsize",
            help="Number of results per query batch",
            default=1000,
            type=int,
        )
        parser.add_argument(
            "--skip_ref",
            help="Skip reference data type",
            action="store_true",
        )
        parser.add_argument(
            "--skip_file",
            help="Skip file data type",
            action="store_true",
        )
        parser.add_argument(
            "--skip_ia",
            help="Skip import application data type",
            action="store_true",
        )
        parser.add_argument(
            "--skip_user",
            help="Skip user data type",
            action="store_true",
        )
        parser.add_argument(
            "--start",
            help="Change start point of the run. <data_type>.<index> e.g. ia.5",
            default=".",
            type=str,
        )

    def handle(self, *args, **options):
        if not settings.ALLOW_DATA_MIGRATION or not settings.APP_ENV == "production":
            raise CommandError("Data migration has not been enabled for this environment")

        self.batch_size = options["batchsize"]
        self.start_type, self.start_index = options["start"].split(".")

    def _get_data_list(self, data_list: list[Any]) -> tuple[int, list[Any]]:
        start = (self.start_index and int(self.start_index)) or 1

        if self.start_index:
            data_list = data_list[start - 1 :]
            self.start_index = ""

        return start, data_list

    def _get_start_type(self, data_type: DATA_TYPE) -> bool:
        if self.start_type:
            data_type_starts = self.DATA_TYPE_START.get(data_type, [])

            if self.start_type not in data_type_starts:
                return False

            self.start_type = ""

        return True
