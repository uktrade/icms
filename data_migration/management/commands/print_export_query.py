import argparse
from collections import OrderedDict
from inspect import getmembers

from django.core.management.base import BaseCommand

from data_migration import queries


class Command(BaseCommand):
    ALL_QUERIES: OrderedDict[str, str] = OrderedDict(
        getmembers(queries, lambda obj: isinstance(obj, str))
    )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
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

        if options["l"]:
            for q in self.ALL_QUERIES:
                if query_name and query_name not in q:
                    continue

                self.stdout.write("\t" + str(q))

            return

        query = self.ALL_QUERIES.get(query_name)

        if not query:
            self.stdout.write(f"Query name {query_name} not found. Use -l to list all query names")
            return

        for line in query.split("\n"):
            self.stdout.write(line)

        return
