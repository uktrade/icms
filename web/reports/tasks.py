from config.celery import app
from web.models import ScheduleReport

from .constants import CELERY_REPORTS_QUEUE_NAME, GENERATE_REPORT_TASK_NAME, ReportType
from .generate import (
    generate_access_request_report,
    generate_firearms_licences_report,
    generate_import_licence_report,
    generate_issued_certificate_report,
    generate_supplementary_firearms_report,
)


@app.task(name=GENERATE_REPORT_TASK_NAME, queue=CELERY_REPORTS_QUEUE_NAME)
def generate_report_task(scheduled_report_pk: int) -> None:
    scheduled_report = ScheduleReport.objects.get(pk=scheduled_report_pk)
    match scheduled_report.report.report_type:
        case ReportType.ISSUED_CERTIFICATES:
            generate_issued_certificate_report(scheduled_report)
        case ReportType.ACCESS_REQUESTS:
            generate_access_request_report(scheduled_report)
        case ReportType.IMPORT_LICENCES:
            generate_import_licence_report(scheduled_report)
        case ReportType.SUPPLEMENTARY_FIREARMS:
            generate_supplementary_firearms_report(scheduled_report)
        case ReportType.FIREARMS_LICENCES:
            generate_firearms_licences_report(scheduled_report)
        case _:
            raise ValueError("Unsupported Report Type")
