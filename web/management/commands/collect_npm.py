import glob
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "copy js dependencies to the configured location"

    def mkdir(self, path):
        if not os.path.isdir(path):
            os.mkdir(path)

    def handle(self, *args, **options):
        self.stdout.write(f"Moving JS Dependencies to {settings.NPM_STATIC_FILES_LOCATION}")
        self.stdout.write(f"using config: {settings.NPM_FILE_PATTERNS}")

        self.stdout.write("\nCopying:")
        self.mkdir(settings.NPM_STATIC_FILES_LOCATION)
        for base, paths in settings.NPM_FILE_PATTERNS.items():
            destination = os.path.join(settings.NPM_STATIC_FILES_LOCATION, base)
            for pattern in paths:
                for file in glob.glob(os.path.join("node_modules", base, pattern)):
                    self.mkdir(destination)
                    print(f"\t{file}\t==>\t{destination}/{os.path.basename(file)}")
                    shutil.copy(file, destination)
