from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = """Drop all tables. ONLY FOR USE IN LOCAL/DEV/STAGING ENVIRONMENTS!"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm-drop-all-tables",
            action="store_true",
            help="You must specify this to enable the command to run",
        )

    def handle(self, *args, **options):
        if settings.APP_ENV not in ("local", "dev", "staging"):
            raise CommandError("Can only drop tables in 'staging', 'dev' and 'local' environments!")

        if not settings.ALLOW_DISASTROUS_DATA_DROPS_NEVER_ENABLE_IN_PROD:
            raise CommandError(
                "You have not enabled danger zone! (https://www.youtube.com/watch?v=siwpn14IE7E)"
            )

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
