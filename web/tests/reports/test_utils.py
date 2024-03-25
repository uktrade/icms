import pytest

from web.reports.constants import ReportType
from web.reports.utils import format_parameters_used


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
                "Legislation": "Biocide Products Regulation 528/2012 as retained in UK law<br>Biocide Products Regulation 528/2012 (EU BPR)",
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
    ),
)
def test_format_parameters_used(report_schedule, report_type, parameters, exp_formatted_parameters):
    report_schedule.report.report_type = report_type
    report_schedule.parameters = parameters
    assert format_parameters_used(report_schedule) == exp_formatted_parameters
