from unittest import mock

import pytest
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from web.models import File, GeneratedReport
from web.reports.constants import (
    DateFilterType,
    ReportStatus,
    ReportType,
    UserDateFilterType,
)
from web.reports.models import Report, ScheduleReport
from web.tests.helpers import CaseURLS


@pytest.fixture
def deleted_report_schedule(ilb_admin_user):
    return ScheduleReport.objects.create(
        report=Report.objects.get(report_type=ReportType.ISSUED_CERTIFICATES),
        title="DELETED report",
        status=ReportStatus.DELETED,
        scheduled_by=ilb_admin_user,
        notes="",
        parameters={
            "date_from": "2010-02-01",
            "date_to": "2024-01-12",
            "date_filter_type": DateFilterType.SUBMITTED,
            "application_type": "",
            "legislation": [],
        },
    )


def get_report_model(report_type):
    return Report.objects.get(report_type=report_type)


def test_ilb_admin_report_list_view(ilb_admin_client):
    response = ilb_admin_client.get(CaseURLS.report_list_view())
    assert response.status_code == 200
    assertContains(response, "Issued Certificates")
    assertContains(response, "Access Request Report for Importers and Exporters")
    assertContains(response, "Import Licence Data Extract Report")
    assertContains(response, "Supplementary firearms information")
    assertContains(response, "Firearms Licences")
    assertTemplateUsed(response, "web/domains/reports/list-view.html")


def test_nca_admin_report_list_view(nca_admin_client):
    response = nca_admin_client.get(CaseURLS.report_list_view())
    assert response.status_code == 200
    assertNotContains(response, "Issued Certificates")
    assertNotContains(response, "Access Request Report for Importers and Exporters")
    assertNotContains(response, "Import Licence Data Extract Report")
    assertContains(response, "Supplementary firearms information")
    assertContains(response, "Firearms Licences")
    assertTemplateUsed(response, "web/domains/reports/list-view.html")


def test_access_denied_run_history_view(nca_admin_client):
    report = get_report_model(ReportType.ISSUED_CERTIFICATES)
    url = CaseURLS.run_history_view(report.pk)
    response = nca_admin_client.get(url)
    assert response.status_code == 403


@pytest.mark.parametrize("show_deleted", (True, False))
def test_run_history_view(ilb_admin_client, report_schedule, deleted_report_schedule, show_deleted):
    report = get_report_model(ReportType.ISSUED_CERTIFICATES)
    url = CaseURLS.run_history_view(report.pk)
    if show_deleted:
        url = url + "?deleted=1"
    response = ilb_admin_client.get(url)
    assert response.status_code == 200
    assertContains(response, "Run History")
    assertContains(response, "Run Report")
    assertContains(response, "test report")
    if show_deleted:
        assertContains(response, "DELETED report")
    else:
        assertNotContains(response, "DELETED report")

    assertTemplateUsed(response, "web/domains/reports/run-history-view.html")


@pytest.mark.parametrize(
    "report_type,post_data",
    (
        (
            ReportType.ISSUED_CERTIFICATES,
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "1-Jan-2022",
                "notes": "",
                "application_type": "CFS",
                "legislation": ["1"],
            },
        ),
        (
            ReportType.ACCESS_REQUESTS,
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "1-Jan-2022",
                "notes": "",
            },
        ),
        (
            ReportType.IMPORT_LICENCES,
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "1-Jan-2022",
                "notes": "",
                "application_type": "SPS",
                "date_filter_type": DateFilterType.CLOSED,
            },
        ),
        (
            ReportType.ACTIVE_USERS,
            {
                "title": "test report",
                "date_from": "1-Jan-2006",
                "date_to": "1-Jan-2022",
                "notes": "",
                "date_filter_type": UserDateFilterType.DATE_JOINED,
            },
        ),
    ),
)
@mock.patch("web.reports.tasks.generate_report_task.delay")
def test_run_report_view(mock_generate_report, ilb_admin_client, report_type, post_data):
    mock_generate_report.return_value = None
    report = get_report_model(report_type)
    response = ilb_admin_client.post(
        CaseURLS.run_report_view(report.pk),
        data=post_data,
    )
    assert response.status_code == 302, response.context["form"].errors
    assert mock_generate_report.called is True
    assert response.headers["location"] == CaseURLS.run_history_view(report.pk)


def test_access_denied_run_report_view(nca_admin_client):
    report = get_report_model(ReportType.ISSUED_CERTIFICATES)
    url = CaseURLS.run_report_view(report.pk)
    response = nca_admin_client.get(url)
    assert response.status_code == 403


@pytest.mark.parametrize(
    "report_type,post_data,expected_errors",
    (
        (
            ReportType.ACCESS_REQUESTS,
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "",
                "notes": "",
                "application_type": "",
            },
            {"date_to": ["You must enter this item"]},
        ),
        (
            ReportType.ISSUED_CERTIFICATES,
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "1-Feb-2024",
                "notes": "",
                "application_type": "",
            },
            {
                "date_to": ["Date range cannot be greater than 2 years"],
                "date_from": ["Date range cannot be greater than 2 years"],
            },
        ),
        (
            ReportType.ISSUED_CERTIFICATES,
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "1-Feb-2019",
                "notes": "",
                "application_type": "",
            },
            {
                "date_to": ["Date cannot be earlier than date from field"],
            },
        ),
        (
            ReportType.ISSUED_CERTIFICATES,
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "1-Feb-2022",
                "notes": "",
                "application_type": "SPS",
            },
            {
                "application_type": [
                    "Select a valid choice. SPS is not one of the available choices."
                ]
            },
        ),
        (
            ReportType.IMPORT_LICENCES,
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "1-Feb-2022",
                "notes": "",
                "application_type": "SPS",
                "date_filter_type": "",
            },
            {
                "date_filter_type": ["You must enter this item"],
            },
        ),
        (
            ReportType.IMPORT_LICENCES,
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "1-Feb-2022",
                "notes": "",
                "application_type": "CFS",
                "date_filter_type": DateFilterType.SUBMITTED,
            },
            {
                "application_type": [
                    "Select a valid choice. CFS is not one of the available choices."
                ]
            },
        ),
        (
            ReportType.ISSUED_CERTIFICATES,
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "1-Jan-2022",
                "notes": "",
                "application_type": "CFS",
                "legislation": ["0"],
            },
            {"legislation": ["Select a valid choice. 0 is not one of the available choices."]},
        ),
    ),
)
@mock.patch("web.reports.tasks.generate_report_task.delay")
def test_run_report_view_form_errors(
    mock_generate_report, ilb_admin_client, report_type, post_data, expected_errors
):
    mock_generate_report.return_value = None
    report = get_report_model(report_type)
    response = ilb_admin_client.get(CaseURLS.run_report_view(report.pk))
    assert response.status_code == 200
    response = ilb_admin_client.post(
        CaseURLS.run_report_view(report.pk),
        data=post_data,
    )
    assert response.status_code == 200
    assert mock_generate_report.called is False
    assert response.context["form"].errors == expected_errors


def test_report_output_view(ilb_admin_client, report_schedule):
    response = ilb_admin_client.get(
        CaseURLS.run_output_view(report_schedule.report.pk, report_schedule.pk)
    )
    assert response.status_code == 200
    assertTemplateUsed(response, "web/domains/reports/run-output-view.html")
    assertContains(response, "Report Output")
    assertContains(response, "Submitted")
    assertContains(response, "Date From")
    assertContains(response, "01 Feb 2010")
    assertContains(response, "Date Filter Type")
    assertContains(response, "Application Submitted date")


def test_access_denied_run_output_view(nca_admin_client, report_schedule):
    response = nca_admin_client.get(
        CaseURLS.run_output_view(report_schedule.report.pk, report_schedule.pk)
    )
    assert response.status_code == 403


def test_report_delete_view(ilb_admin_client, report_schedule):
    response = ilb_admin_client.post(
        CaseURLS.delete_report_view(report_schedule.report.pk, report_schedule.pk), follow=True
    )
    assert response.status_code == 200
    report_schedule.refresh_from_db()
    assert report_schedule.status == ReportStatus.DELETED


@mock.patch("web.reports.views.get_file_from_s3")
def test_download_report_view(
    mock_get_file_from_s3, ilb_admin_client, report_schedule, ilb_admin_user
):
    file_data = b"testdata"
    mock_get_file_from_s3.return_value = file_data
    document = File.objects.create(
        is_active=True,
        filename="test.csv",
        content_type="application/csv",
        file_size=10,
        path="test.csv",
        created_by=ilb_admin_user,
    )
    generated_report = GeneratedReport.objects.create(
        schedule=report_schedule, document=document, status=ReportStatus.COMPLETED
    )

    response = ilb_admin_client.get(
        CaseURLS.download_report_view(report_schedule.report.pk, generated_report.pk)
    )
    assert response.status_code == 200
    assert mock_get_file_from_s3.called is True
    assert response.content == file_data
    assert response.headers["Content-Disposition"] == 'attachment; filename="test.csv"'
