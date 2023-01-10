from django.core.management.base import BaseCommand

from web import models

# TODO ICMSLST-1616 Expand command to cover all relevant models

counts = [
    (
        "Export Variations",
        70,
        models.VariationRequest.objects.filter(exportapplication__isnull=False).count(),
        False,
    ),
    (
        "Import Variations",
        2890,
        models.VariationRequest.objects.filter(importapplication__isnull=False).count(),
        False,
    ),
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        for count in counts:
            self._log_result(*count)

    def _log_result(self, name: str, expected: int, actual: int, exact: bool = False) -> None:
        if exact:
            result = "PASS" if expected == actual else "FAIL"
        else:
            result = "PASS" if expected <= actual else "FAIL"

        self.stdout.write(f"{result} - EXPECTED: {expected} - ACTUAL: {actual}")
