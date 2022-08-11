import argparse

from django.core.management.base import BaseCommand

from data_migration.queries import (
    export_application,
    files,
    import_application,
    reference,
    user,
)


class Command(BaseCommand):
    QUERY_MODULES = [files, import_application, reference, export_application, user]

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "query_name",
            nargs="?",
            help="The name of the query to be printed",
            type=str,
        )
        parser.add_argument(
            "-l",
            help="List all query names",
            action="store_true",
        )

    def handle(self, *args, **options):
        query_name = options["query_name"]

        if options["l"] or not query_name:
            all_queries = sorted(q for mod in self.QUERY_MODULES for q in mod.__all__)

            for q in all_queries:
                self.stdout.write(str(q))

            return

        for mod in self.QUERY_MODULES:
            if query_name in mod.__all__:
                query = str(getattr(mod, query_name))
                for line in query.split("\n"):
                    self.stdout.write(line)

                return

        self.stdout.write(f"Query name {query_name} not found. Use -l to list all query names")
