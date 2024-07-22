import argparse
import time as tm
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from .config.run_order import DATA_TYPE


class MigrationBaseCommand(BaseCommand):
    DATA_TYPE_START: dict[str, list[str]] = {}

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
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
            "--skip_export",
            help="Skip export application data type",
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
        parser.add_argument(
            "--force_log",
            help="Force logs to be written to stdout",
            action="store_true",
        )

    def handle(self, *args, **options):
        if not settings.ALLOW_DATA_MIGRATION:
            raise CommandError("Data migration has not been enabled for this environment")

        self.batch_size = options["batchsize"]
        self.start_type, self.start_index = options["start"].split(".")
        self.start_time = tm.perf_counter()
        self.split_time = tm.perf_counter()
        self.print_log = options["force_log"] or settings.APP_ENV == "production"

    def log(self, message: str, ending: None | str = None) -> None:
        if self.print_log:
            self.stdout.write(message, ending=ending)

    def _log_time(self, count: int | None = None) -> None:
        time_taken = tm.perf_counter() - self.split_time
        prefix = "\t\t--> " if count is None else f"\t\t{count} records --> "

        if time_taken // 60 > 0:
            self.log(f"{prefix}{time_taken // 60:.0f} mins {time_taken % 60:.0f} seconds", "\n\n")
        else:
            self.log(f"{prefix}{time_taken:.2f} seconds", "\n\n")
        self.split_time = tm.perf_counter()

    def _log_script_end(self) -> None:
        time_taken = tm.perf_counter() - self.start_time
        mins = time_taken // 60
        secs = time_taken % 60

        self.log(f"Execution Time --> {mins:.0f} minutes {secs:.0f} seconds", "\n\n")

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
