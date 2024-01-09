from web.models import Report
from web.reports.constants import ReportType

templates = [
    (
        "Issued Certificates",
        "Reports relating to issued Certificates of Free Sale, Certificates of Manufacture and Certificates of Good Manufacturing Practice",
        ReportType.ISSUED_CERTIFICATES,
    )
]


def add_reports():
    Report.objects.bulk_create(
        [
            Report(name=name, description=description, report_type=report_type)
            for name, description, report_type in templates
        ]
    )
