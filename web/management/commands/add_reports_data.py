from django.core.management.base import BaseCommand

from web.models import Report
from web.reports.constants import ReportType

templates = [
    (
        "Issued Certificates",
        "Reports relating to issued Certificates of Free Sale, Certificates of Manufacture and Certificates of Good Manufacturing Practice",
        ReportType.ISSUED_CERTIFICATES,
    ),
    (
        "Access Request Report for Importers and Exporters",
        "Report for Importer / Exporter access request filtering on dates",
        ReportType.ACCESS_REQUESTS,
    ),
    (
        "ICMS Import Licence Data Extract Report",
        "Data extract of import licences filtering on licence type, submitted date and issued date",
        ReportType.IMPORT_LICENCES,
    ),
    (
        "ICMS - Supplementary firearms information",
        "Data extract of import licences filtering on licence type, submitted date and issued date",
        ReportType.SUPPLEMENTARY_FIREARMS,
    ),
    (
        "ICMS - Firearms Licences",
        "Reports relating to ICMS Firearms licences",
        ReportType.FIREARMS_LICENCES,
    ),
]


def add_reports():
    for name, description, report_type in templates:
        Report.objects.get_or_create(
            report_type=report_type,
            defaults={
                "name": name,
                "description": description,
            },
        )


class Command(BaseCommand):
    help = """Create Reports Data"""

    def handle(self, *args, **options):
        add_reports()
