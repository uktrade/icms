from datetime import datetime

import pytest

from web.reports.interfaces import IssuedCertificateReportInterface

EXPECTED_HEADER = [
    "Certificate Reference",
    "Case Reference",
    "Application Type",
    "Submitted Datetime",
    "Issue Datetime",
    "Case Processing Time",
    "Total Processing Time",
    "Exporter",
    "Contact Full Name",
    "Agent",
    "Country",
    "Is Manufacturer",
    "Responsible Person Statement",
    "Countries of Manufacture",
    "Product Legislation",
    "HSE Email Count",
    "BEIS Email Count",
    "Application Update Count",
    "FIR Count",
    "Business Days to Process",
]


def update_submitted_and_completed_dates_on_app(app):
    app.submit_datetime = datetime(2024, 1, 1, 12, 0, 0)
    app.save()
    for cert in app.certificates.all():
        cert.case_completion_datetime = datetime(2024, 1, 9, 13, 7, 0)
        cert.save()


@pytest.mark.django_db
def test_issued_certificate_report_interface_get_data_header(report_schedule):
    interface = IssuedCertificateReportInterface(report_schedule)
    data = interface.get_data()
    assert data == {
        "header": EXPECTED_HEADER,
        "results": [],
    }


@pytest.mark.django_db
def test_issued_certificate_report_interface_get_data_cfs(report_schedule, completed_cfs_app):
    update_submitted_and_completed_dates_on_app(completed_cfs_app)
    interface = IssuedCertificateReportInterface(report_schedule)
    data = interface.get_data()
    assert data["results"] == [
        {
            "Agent": "",
            "Application Type": "Certificate of Free Sale",
            "Application Update Count": 0,
            "BEIS Email Count": 0,
            "Business Days to Process": 7,
            "Case Processing Time": "8d 1h 7m",
            "Case Reference": "CA/2024/00001",
            "Certificate Reference": "CFS/2024/00002",
            "Contact Full Name": "E1_main_contact_first_name E1_main_contact_last_name",
            "Countries of Manufacture": "Afghanistan",
            "Country": "Zimbabwe",
            "Exporter": "Test Exporter 1",
            "FIR Count": 0,
            "HSE Email Count": 0,
            "Is Manufacturer": "Yes",
            "Issue Datetime": "09/01/2024 13:07:00",
            "Product Legislation": "Biocide Products Regulation 528/2012 as retained in UK law",
            "Responsible Person Statement": "Yes",
            "Submitted Datetime": "01/01/2024 12:00:00",
            "Total Processing Time": "8d 1h 7m",
        },
        {
            "Agent": "",
            "Application Type": "Certificate of Free Sale",
            "Application Update Count": 0,
            "BEIS Email Count": 0,
            "Business Days to Process": 7,
            "Case Processing Time": "8d 1h 7m",
            "Case Reference": "CA/2024/00001",
            "Certificate Reference": "CFS/2024/00001",
            "Contact Full Name": "E1_main_contact_first_name E1_main_contact_last_name",
            "Countries of Manufacture": "Afghanistan",
            "Country": "Afghanistan",
            "Exporter": "Test Exporter 1",
            "FIR Count": 0,
            "HSE Email Count": 0,
            "Is Manufacturer": "Yes",
            "Issue Datetime": "09/01/2024 13:07:00",
            "Product Legislation": "Biocide Products Regulation 528/2012 as retained in UK law",
            "Responsible Person Statement": "Yes",
            "Submitted Datetime": "01/01/2024 12:00:00",
            "Total Processing Time": "8d 1h 7m",
        },
    ]


@pytest.mark.django_db
def test_issued_certificate_report_interface_get_data_gmp(report_schedule, completed_gmp_app):
    update_submitted_and_completed_dates_on_app(completed_gmp_app)
    interface = IssuedCertificateReportInterface(report_schedule)
    data = interface.get_data()
    assert data["results"] == [
        {
            "Agent": "",
            "Application Type": "Certificate of Good Manufacturing Practice",
            "Application Update Count": 0,
            "BEIS Email Count": 0,
            "Business Days to Process": 7,
            "Case Processing Time": "8d 1h 7m",
            "Case Reference": "GA/2024/00001",
            "Certificate Reference": "GMP/2024/00001",
            "Contact Full Name": "E1_main_contact_first_name E1_main_contact_last_name",
            "Countries of Manufacture": "",
            "Country": "China",
            "Exporter": "Test Exporter 1",
            "FIR Count": 0,
            "HSE Email Count": 0,
            "Is Manufacturer": "",
            "Issue Datetime": "09/01/2024 13:07:00",
            "Product Legislation": "",
            "Responsible Person Statement": "",
            "Submitted Datetime": "01/01/2024 12:00:00",
            "Total Processing Time": "8d 1h 7m",
        },
    ]


@pytest.mark.django_db
def test_issued_certificate_report_interface_get_data_com(report_schedule, completed_com_app):
    update_submitted_and_completed_dates_on_app(completed_com_app)
    interface = IssuedCertificateReportInterface(report_schedule)
    data = interface.get_data()
    assert data["results"] == [
        {
            "Agent": "",
            "Application Type": "Certificate of Manufacture",
            "Application Update Count": 0,
            "BEIS Email Count": 0,
            "Business Days to Process": 7,
            "Case Processing Time": "8d 1h 7m",
            "Case Reference": "CA/2024/00001",
            "Certificate Reference": "COM/2024/00001",
            "Contact Full Name": "E1_main_contact_first_name E1_main_contact_last_name",
            "Countries of Manufacture": "",
            "Country": "Afghanistan",
            "Exporter": "Test Exporter 1",
            "FIR Count": 0,
            "HSE Email Count": 0,
            "Is Manufacturer": "",
            "Issue Datetime": "09/01/2024 13:07:00",
            "Product Legislation": "",
            "Responsible Person Statement": "",
            "Submitted Datetime": "01/01/2024 12:00:00",
            "Total Processing Time": "8d 1h 7m",
        },
    ]
