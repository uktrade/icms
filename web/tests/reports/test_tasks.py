from unittest import mock

import pytest

from web.models import Report
from web.reports.constants import ReportType
from web.reports.tasks import generate_report_task


def test_report_task(report_schedule):
    for report_type in ReportType:
        report_schedule.report = Report.objects.get(report_type=report_type)
        report_schedule.save()
        with mock.patch("web.reports.generate.write_files") as mock_write_files:
            mock_write_files.return_value = None
            generate_report_task(report_schedule.pk)
            mock_write_files.assert_called_once()


def test_report_task_unsupported(report_schedule):
    report_schedule.report.report_type = "REPORT1"
    report_schedule.report.save()
    with pytest.raises(ValueError, match="Unsupported Report Type"):
        generate_report_task(report_schedule.pk)
