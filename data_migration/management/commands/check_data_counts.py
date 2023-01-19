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
    (
        "OIL Supplementary Report Firearm Uploaded Documents",
        331,
        models.OILSupplementaryReportFirearm.objects.filter(is_upload=True).count(),
        True,
    ),
    (
        "DFL Supplementary Report Firearm Uploaded Documents",
        1,
        models.DFLSupplementaryReportFirearm.objects.filter(is_upload=True).count(),
        True,
    ),
    (
        "SIL Supplementary Report Firearm Uploaded Documents",
        237,
        (
            models.SILSupplementaryReportFirearmSection1.objects.filter(is_upload=True).count()
            + models.SILSupplementaryReportFirearmSection2.objects.filter(is_upload=True).count()
            + models.SILSupplementaryReportFirearmSection5.objects.filter(is_upload=True).count()
            + models.SILSupplementaryReportFirearmSection582Obsolete.objects.filter(  # /PS-IGNORE
                is_upload=True
            ).count()
            + models.SILSupplementaryReportFirearmSection582Other.objects.filter(  # /PS-IGNORE
                is_upload=True
            ).count()
        ),
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


# TODO ICMSLST-1616 Possibly check queries against V1 data directly with xquery
"""
SELECT count(*)
FROM impmgr.import_application_details ad
INNER JOIN impmgr.xview_ima_details xid ON ad.id = xid.imad_id AND ima_sub_type = 'OIL'
CROSS JOIN XMLTABLE('
for $g1 in /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT | <null/>
where /IMA/FA_REPORTS/FA_SUPPLEMENTARY_REPORT_LIST/FA_SUPPLEMENTARY_REPORT and not($g1/self::null)
return
for $g2 in $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE | <null/>
where $g1/FA_SUPPLEMENTARY_REPORT_DETAILS/GOODS_LINE_LIST/GOODS_LINE and not($g2/self::null)
return
for $g3 in $g2/FILE_UPLOAD_LIST/FILE_UPLOAD | <null/>
where $g2/FILE_UPLOAD_LIST/FILE_UPLOAD and not ($g3/self::null)
return
<uploads>
  <file_id>{$g3/FILE_CONTENT/file-id/text()}</file_id>
</uploads>
'
PASSING ad.xml_data
COLUMNS
  file_id VARCHAR(4000) PATH '/uploads/file_id/text()'
) x
WHERE ad.status_control = 'C'
"""
