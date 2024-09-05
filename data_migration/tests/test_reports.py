import datetime as dt
from unittest import mock

import oracledb
import pytest
from django.core.management import call_command

from data_migration import models as dm
from data_migration import queries
from data_migration.management.commands.config.run_order import (
    DATA_TYPE_M2M,
    DATA_TYPE_QUERY_MODEL,
    DATA_TYPE_SOURCE_TARGET,
)
from data_migration.management.commands.types import QueryModel
from web import models as web
from web.reports.constants import ReportType

from . import utils

report_query_model = {
    "user": [QueryModel(queries.users, "users", dm.User)],
    "file_folder": [],
    "file": [
        QueryModel(
            queries.schedule_reports,
            "Schedule Reports",
            dm.ScheduleReport,
        ),
        QueryModel(
            queries.report_files,
            "Generated Report Files",
            dm.GeneratedReport,
        ),
    ],
    "import_application": [],
    "export_application": [],
    "reference": [],
}


report_data_source_target = {
    "user": [
        (dm.User, web.User),
    ],
    "reference": [],
    "import_application": [],
    "export_application": [],
    "file": [
        (dm.ScheduleReport, web.ScheduleReport),
        (dm.GeneratedReport, web.GeneratedReport),
        (dm.File, web.File),
    ],
}


report_m2m = {
    "export_application": [],
    "import_application": [],
    "file": [],
}


@pytest.mark.django_db
@mock.patch.object(oracledb, "connect")
@mock.patch.dict(DATA_TYPE_SOURCE_TARGET, report_data_source_target)
@mock.patch.dict(DATA_TYPE_M2M, report_m2m)
@mock.patch.dict(DATA_TYPE_QUERY_MODEL, report_query_model)
def test_historical_reports(mock_connect, dummy_dm_settings):
    mock_connect.return_value = utils.MockConnect()
    call_command("export_from_v1")
    call_command("import_v1_data")

    assert dm.ScheduleReport.objects.count() == 5
    assert dm.GeneratedReport.objects.count() == 5

    assert web.ScheduleReport.objects.count() == 5
    assert web.GeneratedReport.objects.count() == 5

    dm_gr1 = dm.GeneratedReport.objects.first()
    assert dm_gr1.report_output.path == "REPORTS/LEGACY/200204271223_ISSUED_CERTS.csv"
    assert dm_gr1.report_output.filename == "200204271223_ISSUED_CERTS.csv"
    assert dm_gr1.report_output.content_type == "text/csv"
    assert dm_gr1.report_output.report_output_id == 500

    schedule_reports = web.ScheduleReport.objects.all()
    dm_schedule_reports = dm.ScheduleReport.objects.all()

    sr1 = schedule_reports[0]
    assert sr1.title == "Issued certs report"
    assert sr1.status == "COMPLETED"
    assert sr1.report == web.Report.objects.get(report_type=ReportType.ISSUED_CERTIFICATES)
    assert sr1.scheduled_by_id == 0
    assert sr1.legacy_report_id == 1001
    assert sr1.started_at == dt.datetime(2022, 4, 27, 11, 23, tzinfo=dt.UTC)
    assert sr1.finished_at == dt.datetime(2022, 4, 27, 11, 25, tzinfo=dt.UTC)
    assert sr1.deleted_at is None
    assert sr1.parameters == {
        "application_type": None,
        "case_closed_date_from": None,
        "case_closed_date_to": None,
        "case_submitted_date_from": None,
        "case_submitted_date_to": None,
        "date_from": "2017-06-01",
        "date_to": "2017-06-30",
        "is_legacy_report": True,
    }
    assert sr1.generated_files.count() == 1
    sr1_file = sr1.generated_files.first()
    assert sr1_file.document.path == "REPORTS/LEGACY/200204271223_ISSUED_CERTS.csv"
    assert sr1_file.document.created_by_id == 0

    dm_sr1 = dm_schedule_reports[0]
    assert dm_sr1.scheduled_by_id == 2
    assert dm_sr1.deleted_by_id is None

    sr2 = schedule_reports[1]
    assert sr2.title == "Issued licences report"
    assert sr2.status == "COMPLETED"
    assert sr2.report == web.Report.objects.get(report_type=ReportType.IMPORT_LICENCES)
    assert sr2.scheduled_by_id == 0
    assert sr2.legacy_report_id == 1002
    assert sr2.started_at == dt.datetime(2022, 4, 27, 11, 23, tzinfo=dt.UTC)
    assert sr2.finished_at == dt.datetime(2022, 4, 27, 11, 25, tzinfo=dt.UTC)
    assert sr2.deleted_at is None
    assert sr2.parameters == {
        "application_type": None,
        "date_from": None,
        "date_to": None,
        "case_submitted_date_from": "2017-06-01",
        "case_submitted_date_to": "2017-06-30",
        "case_closed_date_from": "2017-06-01",
        "case_closed_date_to": "2017-06-30",
        "is_legacy_report": True,
    }
    assert sr2.generated_files.count() == 1
    sr2_file = sr2.generated_files.first()
    assert sr2_file.document.path == "REPORTS/LEGACY/200204271223_ISSUED_LICENCES.csv"
    assert sr2_file.document.created_by_id == 0

    dm_sr2 = dm_schedule_reports[1]
    assert dm_sr2.scheduled_by_id == 2
    assert dm_sr2.deleted_by_id is None

    sr3 = schedule_reports[2]
    assert sr3.title == "Access request report"
    assert sr3.status == "DELETED"
    assert sr3.report == web.Report.objects.get(report_type=ReportType.ACCESS_REQUESTS)
    assert sr3.scheduled_by_id == 0
    assert sr3.legacy_report_id == 1003
    assert sr3.started_at == dt.datetime(2022, 4, 27, 11, 23, tzinfo=dt.UTC)
    assert sr3.finished_at == dt.datetime(2022, 4, 27, 11, 25, tzinfo=dt.UTC)
    assert sr3.deleted_at == dt.datetime(2022, 4, 30, 8, 0, tzinfo=dt.UTC)
    assert sr3.deleted_by_id == 0
    assert sr3.parameters == {
        "application_type": None,
        "case_closed_date_from": None,
        "case_closed_date_to": None,
        "case_submitted_date_from": None,
        "case_submitted_date_to": None,
        "date_from": "2020-02-01",
        "date_to": "2020-03-30",
        "is_legacy_report": True,
    }
    assert sr3.generated_files.count() == 1
    sr3_file = sr3.generated_files.first()
    assert sr3_file.document.path == "REPORTS/LEGACY/200204271223_ACCESS_REQUESTS.csv"
    assert sr3_file.document.created_by_id == 0

    dm_sr3 = dm_schedule_reports[2]
    assert dm_sr3.scheduled_by_id == 2
    assert dm_sr3.deleted_by_id == 3

    sr4 = schedule_reports[3]
    assert sr4.title == "NCA report"
    assert sr4.status == "COMPLETED"
    assert sr4.report == web.Report.objects.get(report_type=ReportType.SUPPLEMENTARY_FIREARMS)
    assert sr4.scheduled_by_id == 0
    assert sr4.legacy_report_id == 1004
    assert sr4.generated_files.count() == 1
    sr4_file = sr4.generated_files.first()
    assert sr4_file.document.path == "REPORTS/LEGACY/200204271223_NCA_REPORT.csv"
    assert sr4_file.document.created_by_id == 0

    dm_sr4 = dm_schedule_reports[3]
    assert dm_sr4.scheduled_by_id == 2
    assert dm_sr4.deleted_by_id is None

    sr5 = schedule_reports[4]
    assert sr5.title == "Firearms report"
    assert sr5.status == "COMPLETED"
    assert sr5.report == web.Report.objects.get(report_type=ReportType.FIREARMS_LICENCES)
    assert sr5.scheduled_by_id == 0
    assert sr5.legacy_report_id == 1005
    assert sr5.generated_files.count() == 1
    sr5_file = sr5.generated_files.first()
    assert sr5_file.document.path == "REPORTS/LEGACY/200204271223_FIREARMS.csv"
    assert sr5_file.document.created_by_id == 0

    dm_sr5 = dm_schedule_reports[4]
    assert dm_sr5.scheduled_by_id == 3
    assert dm_sr5.deleted_by_id is None
