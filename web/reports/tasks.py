from config.celery import app
from web.models import ScheduleReport

from .generate import generate_issued_certificate_report


@app.task
def generate_issued_certificate_report_task(scheduled_report_pk):
    scheduled_report = ScheduleReport.objects.get(pk=scheduled_report_pk)
    generate_issued_certificate_report(scheduled_report)
