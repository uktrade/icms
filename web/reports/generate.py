import csv
from io import StringIO

from django.utils import timezone

from web.models import File, GeneratedReport, ScheduleReport
from web.utils.s3 import put_object_in_s3
from web.utils.spreadsheet import XlsxConfig, generate_xlsx_file

from .constants import ReportStatus
from .interfaces import IssuedCertificateReportInterface


def get_report_file_name(scheduled_report: ScheduleReport) -> str:
    return f"{scheduled_report.report.name}-{scheduled_report.title}-{scheduled_report.pk}"


def generate_issued_certificate_report(scheduled_report: ScheduleReport) -> None:
    report_interface = IssuedCertificateReportInterface(scheduled_report)
    scheduled_report.status = ReportStatus.IN_PROGRESS
    scheduled_report.started_at = timezone.now()
    scheduled_report.save()

    write_files(report_interface)
    scheduled_report.status = ReportStatus.COMPLETED
    scheduled_report.finished_at = timezone.now()
    scheduled_report.save()


def write_files(report_interface: IssuedCertificateReportInterface) -> None:
    scheduled_report = report_interface.scheduled_report
    data = report_interface.get_data()
    file_name = get_report_file_name(scheduled_report)
    _write_csv_file(scheduled_report, file_name, data["results"], data["header"])
    _write_xlsx_file(scheduled_report, file_name, data["results"], data["header"])


def _write_xlsx_file(
    scheduled_report: ScheduleReport, file_name: str, data: list, header: list
) -> None:
    file_name = f"{file_name}.xlsx"
    config = XlsxConfig()
    config.header.data = header
    config.header.styles = {"bold": True}
    config.rows = [d.values() for d in data]
    config.column_width = 25
    config.sheet_name = "Sheet 1"
    file_data = generate_xlsx_file(config, {"remove_timezone": True})
    write_file_data(
        scheduled_report,
        file_data,
        file_name,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _write_csv_file(
    scheduled_report: ScheduleReport, file_name: str, data: list, header: list
) -> None:
    file_name = f"{file_name}.csv"
    dest = StringIO()
    writer = csv.DictWriter(dest, header)
    writer.writeheader()
    writer.writerows(data)
    write_file_data(scheduled_report, dest.getvalue(), file_name, "application/csv")
    dest.close()


def write_file_data(
    scheduled_report: ScheduleReport, data: str | bytes, file_name: str, content_type: str
) -> GeneratedReport:
    path = f"REPORTS/{scheduled_report.report.pk}/{file_name}"
    file_size = put_object_in_s3(data, path)
    document = File.objects.create(
        is_active=True,
        filename=file_name,
        content_type=content_type,
        file_size=file_size,
        path=path,
        created_by=scheduled_report.scheduled_by,
    )
    return GeneratedReport.objects.create(
        schedule=scheduled_report, document=document, status=ReportStatus.COMPLETED
    )
