from unittest import mock

import pytest
from pytest_django.asserts import assertContains, assertTemplateUsed

from web.models import File, GeneratedReport
from web.reports.constants import ReportStatus, ReportType
from web.reports.models import Report
from web.tests.helpers import CaseURLS


def get_issued_certificates_report_model():
    return Report.objects.get(report_type=ReportType.ISSUED_CERTIFICATES)


def test_report_list_view(report_user_client):
    response = report_user_client.get(CaseURLS.report_list_view())
    assert response.status_code == 200
    assertContains(response, "Issued Certificates")
    assertTemplateUsed(response, "web/domains/reports/list-view.html")


def test_run_history_view(report_user_client):
    report = get_issued_certificates_report_model()
    response = report_user_client.get(CaseURLS.run_history_view(report.pk))
    assert response.status_code == 200
    assertContains(response, "Run History")
    assertContains(response, "Run Report")
    assertTemplateUsed(response, "web/domains/reports/run-history-view.html")


@mock.patch("web.reports.tasks.generate_issued_certificate_report_task.delay")
def test_run_report_view(mock_generate_report, report_user_client):
    mock_generate_report.return_value = None
    report = get_issued_certificates_report_model()
    response = report_user_client.post(
        CaseURLS.run_report_view(report.pk),
        data={
            "title": "test report",
            "date_from": "1-Jan-2022",
            "date_to": "1-Jan-2022",
            "notes": "",
        },
    )
    assert response.status_code == 302
    assert mock_generate_report.called is True
    assert response.headers["location"] == CaseURLS.run_history_view(report.pk)


@pytest.mark.parametrize(
    "post_data,expected_errors",
    (
        (
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
            {
                "title": "test report",
                "date_from": "1-Jan-2022",
                "date_to": "1-Feb-2022",
                "notes": "",
                "application_type": "TEST",
            },
            {
                "application_type": [
                    "Select a valid choice. TEST is not one of the available choices."
                ]
            },
        ),
    ),
)
@mock.patch("web.reports.tasks.generate_issued_certificate_report_task.delay")
def test_run_report_view_form_errors(
    mock_generate_report, report_user_client, post_data, expected_errors
):
    mock_generate_report.return_value = None
    report = get_issued_certificates_report_model()
    response = report_user_client.get(CaseURLS.run_report_view(report.pk))
    assert response.status_code == 200
    response = report_user_client.post(
        CaseURLS.run_report_view(report.pk),
        data=post_data,
    )
    assert response.status_code == 200
    assert mock_generate_report.called is False
    assert response.context["form"].errors == expected_errors


def test_report_output_view(report_user_client, report_schedule):
    response = report_user_client.get(
        CaseURLS.run_output_view(report_schedule.report.pk, report_schedule.pk)
    )
    assert response.status_code == 200
    assertTemplateUsed(response, "web/domains/reports/run-output-view.html")
    assertContains(response, "Report Output")
    assertContains(response, "Submitted")


@mock.patch("web.reports.views.get_file_from_s3")
def test_download_report_view(
    mock_get_file_from_s3, report_user_client, report_schedule, report_user
):
    file_data = b"testdata"
    mock_get_file_from_s3.return_value = file_data
    document = File.objects.create(
        is_active=True,
        filename="test.csv",
        content_type="application/csv",
        file_size=10,
        path="test.csv",
        created_by=report_user,
    )
    generated_report = GeneratedReport.objects.create(
        schedule=report_schedule, document=document, status=ReportStatus.COMPLETED
    )

    response = report_user_client.get(
        CaseURLS.download_report_view(report_schedule.report.pk, generated_report.pk)
    )
    assert response.status_code == 200
    assert mock_get_file_from_s3.called is True
    assert response.content == file_data
    assert response.headers["Content-Disposition"] == 'attachment; filename="test.csv"'
