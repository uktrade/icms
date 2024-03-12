from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = """Drop all tables. Only for use before go live."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm-drop-all-tables",
            action="store_true",
            help="You must specify this to enable the command to run",
        )

    def handle(self, *args, **options):
        if not options["confirm_drop_all_tables"]:
            raise CommandError("Command line parameter not set!")

        cursor = connection.cursor()

        cursor.execute(
            """
              select 'drop table if exists "' || tablename || '" cascade;'
                from pg_tables
                where
                  schemaname = 'public'
                  and tableowner != 'rdsadmin'
                order by tablename;
        """
        )

        rows = cursor.fetchall()

        for row in rows:
            sql = row[0]
            self.stdout.write(f"Executing this SQL: {sql}")
            cursor.execute(sql)

        self.stdout.write("Dropped all tables")
