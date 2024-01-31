from config.celery import app
from web.models import ScheduleReport

from .constants import ReportType
from .generate import generate_access_request_report, generate_issued_certificate_report


@app.task
def generate_report_task(scheduled_report_pk):
    scheduled_report = ScheduleReport.objects.get(pk=scheduled_report_pk)
    match scheduled_report.report.report_type:
        case ReportType.ISSUED_CERTIFICATES:
            generate_issued_certificate_report(scheduled_report)
        case ReportType.ACCESS_REQUESTS:
            generate_access_request_report(scheduled_report)
        case _:
            raise ValueError("Unsupported Report Type")
