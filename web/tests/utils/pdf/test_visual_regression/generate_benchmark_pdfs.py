"""These tests generate benchmark PDFs for visual regression testing.

They are not really tests and as such are not ran as part of the test suite. The reason they are written as tests is
that they depend on pytest fixtures to populate the data needed to produce the PDFs."""

import datetime as dt
import json

import pytest

from web.tests.utils.pdf.test_visual_regression import (
    BENCHMARK_PDF_DIRECTORY,
    date_created_json_file,
)
from web.types import DocumentTypes
from web.utils.pdf import PdfGenerator, StaticPdfGenerator


@pytest.fixture(autouse=True, scope="session")
def save_timestamp():
    """Create a new 'dates_created.json' file so that we can store the time each benchmark PDF was created, so we can
    freeze time when generating the PDFs during test.

    We run this at the start of the session to ensure that the file is there."""

    if not date_created_json_file.exists():
        date_stamp_dict = {}
        date_created_json_file.write_text(json.dumps(date_stamp_dict))
    yield


def update_timestamp(file_name: str) -> None:
    """Update the timestamp for the benchmark PDF in the 'dates_created.json' file."""
    date_stamp_dict = json.loads(date_created_json_file.read_text())
    date_stamp_dict[file_name] = dt.datetime.now().isoformat()
    date_created_json_file.write_text(json.dumps(date_stamp_dict))


def _generate_licence_benchmark_pdf(app, file_name):
    generator = PdfGenerator(DocumentTypes.LICENCE_SIGNED, app, app.licences.first())
    (BENCHMARK_PDF_DIRECTORY / file_name).write_bytes(generator.get_pdf())
    update_timestamp(file_name)


def _generate_certificate_benchmark_pdf(app, file_name):
    country = app.countries.first()
    certificate = app.certificates.first()

    certificate.case_completion_datetime = None
    certificate.save()

    generator = PdfGenerator(DocumentTypes.CERTIFICATE_SIGNED, app, certificate, country)
    (BENCHMARK_PDF_DIRECTORY / file_name).write_bytes(generator.get_pdf())
    update_timestamp(file_name)


def test_generate_benchmark_cfs_certificate(completed_cfs_app):
    _generate_certificate_benchmark_pdf(completed_cfs_app, "cfs_certificate.pdf")


def test_generate_benchmark_com_certificate(completed_com_app):
    _generate_certificate_benchmark_pdf(completed_com_app, "com_certificate.pdf")


def test_generate_benchmark_gmp_certificate(completed_gmp_app):
    _generate_certificate_benchmark_pdf(completed_gmp_app, "gmp_certificate.pdf")


def test_generate_benchmark_oil_licence(completed_oil_app):
    _generate_licence_benchmark_pdf(completed_oil_app, "oil_licence.pdf")


def test_generate_benchmark_dfl_licence(completed_dfl_app):
    _generate_licence_benchmark_pdf(completed_dfl_app, "dfl_licence.pdf")


def test_generate_benchmark_sil_licence(completed_sil_app):
    _generate_licence_benchmark_pdf(completed_sil_app, "sil_licence.pdf")


def test_generate_benchmark_sanctions_licence(completed_sanctions_app):
    _generate_licence_benchmark_pdf(completed_sanctions_app, "sanctions_licence.pdf")


def test_generate_benchmark_cfs_cover_letter():
    file_name = "cfs_cover_letter.pdf"

    generator = StaticPdfGenerator(DocumentTypes.CFS_COVER_LETTER)
    (BENCHMARK_PDF_DIRECTORY / file_name).write_bytes(generator.get_pdf())
    update_timestamp(file_name)


def test_generate_benchmark_cover_letter(completed_dfl_app):
    file_name = "cover_letter.pdf"

    completed_dfl_app.cover_letter_text = "Hello\n" * 500
    generator = PdfGenerator(
        DocumentTypes.COVER_LETTER_SIGNED,
        completed_dfl_app,
        completed_dfl_app.licences.first(),
    )
    (BENCHMARK_PDF_DIRECTORY / file_name).write_bytes(generator.get_pdf())
    update_timestamp(file_name)
