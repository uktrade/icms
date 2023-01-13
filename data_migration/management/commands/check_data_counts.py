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
    (
        "Firearms Acts",
        7,
        models.FirearmsAct.objects.count(),
        True,
    ),
    (
        "Section 5 Clauses",
        17,
        models.Section5Clause.objects.count(),
        True,
    ),
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        passes = 0
        failures = 0

        for count in counts:
            result = self._log_result(*count)

            if result:
                passes += 1
            else:
                failures += 1

        self.stdout.write(f"TOTAL PASS: {passes} - TOTAL FAIL: {failures}")

    def _log_result(self, name: str, expected: int, actual: int, exact: bool = False) -> bool:
        if exact:
            result = "PASS" if expected == actual else "FAIL"
        else:
            result = "PASS" if expected <= actual else "FAIL"

        self.stdout.write(f"{name} - {result} - EXPECTED: {expected} - ACTUAL: {actual}")

        return result == "PASS"
