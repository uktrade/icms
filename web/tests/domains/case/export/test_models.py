import pytest

from web.domains.case.shared import ImpExpStatus
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    ExportApplicationType,
    Process,
)


@pytest.mark.parametrize(
    "application_model",
    [
        CertificateOfManufactureApplication,
        CertificateOfFreeSaleApplication,
        CertificateOfGoodManufacturingPracticeApplication,
    ],
)
@pytest.mark.django_db
def test_export_downcast(application_model, exporter, exporter_one_contact):
    obj = application_model.objects.create(
        # this is not important for this test, so just hardcode it
        application_type=ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.FREE_SALE
        ),
        created_by=exporter_one_contact,
        last_updated_by=exporter_one_contact,
        exporter=exporter,
        exporter_office=exporter.offices.first(),
        process_type=application_model.PROCESS_TYPE,
    )

    # if we already have the specific model, downcast should be a no-op
    assert id(obj) == id(obj.get_specific_model())

    # if we don't, it should load the correct type from the db, and it should be a new instance
    p = Process.objects.get(pk=obj.pk)

    downcast = p.get_specific_model()
    assert type(downcast) is application_model
    assert id(obj) != id(downcast)


def test_display_status_for_submitted_app(com_app_submitted):
    assert com_app_submitted.is_import_application() is False
    assert com_app_submitted.get_status_display() == "Submitted"
    com_app_submitted.status = ImpExpStatus.VARIATION_REQUESTED
    assert com_app_submitted.get_status_display() == "Case Variation"


def test_display_status_for_rejected_app(complete_rejected_export_app):
    assert complete_rejected_export_app.is_import_application() is False
    assert complete_rejected_export_app.get_status_display() == "Completed (Refused)"


def test_display_status_for_in_progress_app(com_app_in_progress):
    assert com_app_in_progress.is_import_application() is False
    assert com_app_in_progress.get_status_display() == "In Progress"
