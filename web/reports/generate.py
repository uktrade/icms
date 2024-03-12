import csv
from io import StringIO

from django.utils import timezone

from web.models import File, GeneratedReport, ScheduleReport
from web.utils.s3 import put_object_in_s3
from web.utils.spreadsheet import MIMETYPE, XlsxSheetConfig, generate_xlsx_file

from .constants import ReportStatus
from .interfaces import (
    AccessRequestTotalsInterface,
    ExporterAccessRequestInterface,
    ImporterAccessRequestInterface,
    ImportLicenceInterface,
    IssuedCertificateReportInterface,
    ReportInterface,
    SupplementaryFirearmsInterface,
)


def get_report_file_name(scheduled_report: ScheduleReport) -> str:
    return f"{scheduled_report.pk}-{scheduled_report.title}"


def _start_processing_report(scheduled_report: ScheduleReport) -> ScheduleReport:
    scheduled_report.status = ReportStatus.IN_PROGRESS
    scheduled_report.started_at = timezone.now()
    scheduled_report.save()
    return scheduled_report


def _end_processing_report(scheduled_report: ScheduleReport) -> None:
    scheduled_report.status = ReportStatus.COMPLETED
    scheduled_report.finished_at = timezone.now()
    scheduled_report.save()


def generate_issued_certificate_report(scheduled_report: ScheduleReport) -> None:
    scheduled_report = _start_processing_report(scheduled_report)
    report_interface = IssuedCertificateReportInterface(scheduled_report)
    write_files(scheduled_report, [report_interface])
    _end_processing_report(scheduled_report)


def generate_supplementary_firearms_report(scheduled_report: ScheduleReport) -> None:
    scheduled_report = _start_processing_report(scheduled_report)
    report_interface = SupplementaryFirearmsInterface(scheduled_report)
    write_files(scheduled_report, [report_interface])
    _end_processing_report(scheduled_report)


def generate_access_request_report(scheduled_report: ScheduleReport) -> None:
    scheduled_report = _start_processing_report(scheduled_report)

    import_report_interface = ImporterAccessRequestInterface(scheduled_report)
    export_report_interface = ExporterAccessRequestInterface(scheduled_report)
    totals = AccessRequestTotalsInterface(scheduled_report)
    write_files(scheduled_report, [import_report_interface, export_report_interface, totals])

    _end_processing_report(scheduled_report)


def generate_import_licence_report(scheduled_report: ScheduleReport) -> None:
    scheduled_report = _start_processing_report(scheduled_report)
    report_interface = ImportLicenceInterface(scheduled_report)
    write_files(scheduled_report, [report_interface])
    _end_processing_report(scheduled_report)


def write_files(scheduled_report: ScheduleReport, report_interfaces: list[ReportInterface]) -> None:
    workbook_sheets = []
    for report_interface in report_interfaces:
        data = report_interface.get_data()
        csv_file_name = f"{scheduled_report.pk}_{report_interface.name}--{scheduled_report.title}"
        _write_csv_file(scheduled_report, csv_file_name, data["results"], data["header"])
        workbook_sheets.append(
            _prepare_workbook_sheet(report_interface.name, data["results"], data["header"])
        )
    file_name = f"{scheduled_report.pk}_{scheduled_report.report.report_type.title()}--{scheduled_report.title}"
    _write_xlsx_file(scheduled_report, file_name, workbook_sheets)


def _prepare_workbook_sheet(sheet_name: str, data: list, header: list) -> XlsxSheetConfig:
    config = XlsxSheetConfig()
    config.header.data = header
    config.header.styles = {"bold": True}
    config.rows = [d.values() for d in data]
    config.column_width = 25
    config.sheet_name = sheet_name
    return config


def _write_xlsx_file(
    scheduled_report: ScheduleReport, file_name: str, sheets: list[XlsxSheetConfig]
) -> None:
    file_name = f"{file_name}.xlsx"
    file_data = generate_xlsx_file(sheets, {"remove_timezone": True})
    write_file_data(scheduled_report, file_data, file_name, MIMETYPE.XLSX)


def _write_csv_file(
    scheduled_report: ScheduleReport, file_name: str, data: list, header: list
) -> None:
    file_name = f"{file_name}.csv"
    dest = StringIO()
    writer = csv.DictWriter(dest, header)
    writer.writeheader()
    writer.writerows(data)
    write_file_data(scheduled_report, dest.getvalue(), file_name, MIMETYPE.CSV)
    dest.close()


def write_file_data(
    scheduled_report: ScheduleReport, data: str | bytes, file_name: str, content_type: MIMETYPE
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
