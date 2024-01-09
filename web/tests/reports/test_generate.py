import datetime
from unittest import mock

from freezegun import freeze_time

from web.models import GeneratedReport
from web.reports import generate
from web.reports.constants import ReportStatus
from web.reports.interfaces import IssuedCertificateReportInterface


def test_get_report_file_name(report_schedule):
    assert (
        generate.get_report_file_name(report_schedule)
        == f"Issued Certificates-test report-{report_schedule.pk}"
    )


@freeze_time("2024-01-01 12:00:00")
@mock.patch("web.reports.generate.write_files")
def test_generate_issued_certificate_report(mock_write_files, report_schedule):
    mock_write_files.return_value = None
    generate.generate_issued_certificate_report(report_schedule)
    assert mock_write_files.called is True
    report_schedule.refresh_from_db()
    assert report_schedule.status == ReportStatus.COMPLETED
    assert report_schedule.started_at == datetime.datetime(
        2024, 1, 1, 12, 0, 0, tzinfo=datetime.UTC
    )
    assert report_schedule.finished_at == datetime.datetime(
        2024, 1, 1, 12, 0, 0, tzinfo=datetime.UTC
    )


@mock.patch("web.reports.generate._write_xlsx_file")
@mock.patch("web.reports.generate._write_csv_file")
def test_write_files(mock_write_csv, mock_write_xlsx, report_schedule):
    mock_write_csv.return_value = None
    mock_write_xlsx.return_value = None
    report_interface = IssuedCertificateReportInterface(report_schedule)
    generate.write_files(report_interface)
    assert mock_write_csv.called is True
    assert mock_write_xlsx.called is True


@freeze_time("2024-01-01 12:00:00")
@mock.patch("web.reports.generate.write_file_data")
def test_write_csv_file(mock_write_file_data, report_schedule):
    mock_write_file_data.return_value = None
    file_data = [{"int": 1, "str": "test", "date": datetime.datetime.now()}]
    generate._write_csv_file(report_schedule, "test-file", file_data, ["int", "str", "date"])
    assert mock_write_file_data.called is True
    assert mock_write_file_data.call_args == mock.call(
        report_schedule,
        "int,str,date\r\n1,test,2024-01-01 12:00:00\r\n",
        "test-file.csv",
        "application/csv",
    )


@freeze_time("2024-01-01 12:00:00")
@mock.patch("web.reports.generate.write_file_data")
def test_write_xlsx_file(mock_write_file_data, report_schedule):
    mock_write_file_data.return_value = None
    file_data = [{"int": 1, "str": "test", "date": datetime.datetime.now()}]
    generate._write_xlsx_file(report_schedule, "test-file", file_data, ["int", "str", "date"])
    assert mock_write_file_data.called is True
    assert mock_write_file_data.call_args == mock.call(
        report_schedule,
        mock.ANY,
        "test-file.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@mock.patch("web.reports.generate.put_object_in_s3")
def test_write_file_data(mock_put_object, report_schedule):
    mock_put_object.return_value = 1234
    generated_report: GeneratedReport = generate.write_file_data(
        report_schedule, "hello", "test-file.txt", "text/html"
    )
    report_schedule.refresh_from_db()
    assert generated_report.status == ReportStatus.COMPLETED
    assert report_schedule.status == ReportStatus.SUBMITTED
    assert generated_report.document.file_size == 1234
    assert generated_report.document.filename == "test-file.txt"
