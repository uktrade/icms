import pytest

from web.reports.constants import ReportType
from web.reports.utils import (
    format_parameters_used,
    get_error_serializer_header,
    get_report_objects_for_user,
    get_variation_number,
)


@pytest.mark.parametrize(
    "report_type,parameters,exp_formatted_parameters",
    (
        (
            ReportType.ISSUED_CERTIFICATES,
            {
                "date_from": "2011-02-03",
                "date_to": "2014-11-16",
                "application_type": "GMP",
                "legislation": [2, 3],
            },
            {
                "Date From": "03 Feb 2011",
                "Date to": "16 Nov 2014",
                "Application Type": "Certificate of Good Manufacturing Practice",
                "Legislation": "Aerosol Dispensers Directive 75/324/EEC<br>Biocide Products Regulation 528/2012 (EU BPR)",
            },
        ),
        (
            ReportType.ACCESS_REQUESTS,
            {
                "date_from": None,
                "date_to": None,
                "case_closed_date_from": "2015-02-01",
                "case_closed_date_to": "2015-02-01",
                "case_submitted_date_from": "2015-02-01",
                "case_submitted_date_to": "2015-02-01",
                "application_type": "My Report",
                "is_legacy_report": True,
            },
            {
                "Date From": "",
                "Date to": "",
                "Case Closed Date From": "01 Feb 2015",
                "Case Closed Date to": "01 Feb 2015",
                "Case Submitted Date From": "01 Feb 2015",
                "Case Submitted Date to": "01 Feb 2015",
                "Application Type": "My Report",
                "Is Legacy Report": "Yes",
            },
        ),
        (
            ReportType.IMPORT_LICENCES,
            {
                "date_from": "2011-02-03",
                "date_to": "2014-11-16",
                "application_type": "FA",
                "date_filter_type": "SUBMITTED",
                "new_field": "Test",
            },
            {
                "Date From": "03 Feb 2011",
                "Date to": "16 Nov 2014",
                "Application Type": "Firearms and Ammunition",
                "Date Filter Type": "Application Submitted date",
                "New Field": "Test",
            },
        ),
        (
            ReportType.ACTIVE_USERS,
            {
                "date_from": "2011-02-03",
                "date_to": "2014-11-16",
                "date_filter_type": "LAST_LOGIN",
                "new_field": "Test",
            },
            {
                "Date From": "03 Feb 2011",
                "Date to": "16 Nov 2014",
                "Date Filter Type": "Last login date",
                "New Field": "Test",
            },
        ),
    ),
)
def test_format_parameters_used(report_schedule, report_type, parameters, exp_formatted_parameters):
    report_schedule.report.report_type = report_type
    report_schedule.parameters = parameters
    assert format_parameters_used(report_schedule) == exp_formatted_parameters


def test_get_error_serializer_header():
    assert get_error_serializer_header() == [
        "Report Name",
        "Identifier",
        "Error Type",
        "Error Message",
        "Column",
        "Value",
    ]


@pytest.mark.parametrize(
    "reference,expected_variation_number",
    (
        ("hello", 0),
        ("IMA/2020/0002/1", 1),
        (None, 0),
    ),
)
def test_get_variation_number(reference, expected_variation_number):
    assert get_variation_number(reference) == expected_variation_number


def test_get_report_objects_for_ilb_admin_user(ilb_admin_user):
    queryset = get_report_objects_for_user(ilb_admin_user)
    assert set(queryset.values_list("report_type", flat=True)) == {
        ReportType.ISSUED_CERTIFICATES,
        ReportType.FIREARMS_LICENCES,
        ReportType.ACCESS_REQUESTS,
        ReportType.SUPPLEMENTARY_FIREARMS,
        ReportType.IMPORT_LICENCES,
        ReportType.ACTIVE_USERS,
    }


def test_get_report_objects_for_nca_admin_user(nca_admin_user):
    queryset = get_report_objects_for_user(nca_admin_user)
    assert set(queryset.values_list("report_type", flat=True)) == {
        ReportType.FIREARMS_LICENCES,
        ReportType.SUPPLEMENTARY_FIREARMS,
    }


def test_get_report_objects_for_ho_admin_user(ho_admin_user):
    queryset = get_report_objects_for_user(ho_admin_user)
    assert set(queryset.values_list("report_type", flat=True)) == set()
