import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "install js dependencies"

    def handle(self, *args, **options):
        self.stdout.write("Installing JS Dependencies")

        os.system("npm install")
