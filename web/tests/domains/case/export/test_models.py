import pytest

from web.domains.case.export.models import ExportApplicationType
from web.flow.models import Process
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
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
def test_export_downcast(application_model, exporter, test_export_user):
    obj = application_model.objects.create(
        # this is not important for this test, so just hardcode it
        application_type=ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.FREE_SALE
        ),
        created_by=test_export_user,
        last_updated_by=test_export_user,
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
