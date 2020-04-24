import os
import glob
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'install js dependencies'

    def mkdir(self, path):
        if not os.path.isdir(path):
            os.mkdir(path)

    def handle(self, *args, **options):
        self.stdout.write(f'Moving JS Dependencies to {settings.NPM_STATIC_FILES_LOCATION}')
        self.stdout.write(f'using config: {settings.NPM_FILE_PATTERNS}')

        self.mkdir(settings.NPM_STATIC_FILES_LOCATION)

        self.stdout.write("\nCopying:")
        for base, paths in settings.NPM_FILE_PATTERNS.items():
            for pattern in paths:
                for file in glob.glob(os.path.join('node_modules', base, pattern)):
                    destination = os.path.join(settings.NPM_STATIC_FILES_LOCATION, base)

                    self.mkdir(destination)
                    print(f"\t{file}\t==>\t{destination}/{os.path.basename(file)}")
                    shutil.copy(file, destination)
