from unittest.mock import Mock

import pytest

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.models import (
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    Country,
    ExportApplicationType,
    GMPBrand,
    ImportApplicationType,
    SILApplication,
)


@pytest.fixture
def lock_manager():
    return Mock()


@pytest.fixture
def fa_sil(db, test_import_user, importer, office):
    """Fake FA-SIL app to test document pack service.

    This application is in PROCESSING state.
    """

    app = SILApplication.objects.create(
        process_type=SILApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type="FA", sub_type="SIL"),
        created_by=test_import_user,
        last_updated_by=test_import_user,
        importer=importer,
        importer_office=office,
        status=ImpExpStatus.PROCESSING,
        reference="IMI/2022/12345",
    )

    return app


@pytest.fixture
def com(db, test_export_user, exporter, exporter_office):
    """Fake COM app to test document pack service.

    This application is in PROCESSING state.
    """

    app = CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code="CFS"),
        created_by=test_export_user,
        last_updated_by=test_export_user,
        exporter=exporter,
        exporter_office=exporter_office,
        status=ImpExpStatus.PROCESSING,
        reference="COM/2022/12345",
    )

    return app


@pytest.fixture
def iar(import_access_request_application):
    """Fixture just to shorten name"""
    return import_access_request_application


@pytest.fixture
def fa_sil_with_draft(fa_sil):
    document_pack.pack_draft_create(fa_sil)

    return fa_sil


@pytest.fixture
def com_with_draft(com):
    document_pack.pack_draft_create(com)

    com.countries.add(Country.objects.get(name="Finland"))
    com.countries.add(Country.objects.get(name="Germany"))

    return com


@pytest.fixture
def gmp_with_draft(db, test_export_user, exporter, exporter_office):
    """Fake COM app to test document pack service.

    This application is in PROCESSING state.
    """

    app = CertificateOfGoodManufacturingPracticeApplication.objects.create(
        process_type=CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code="GMP"),
        created_by=test_export_user,
        last_updated_by=test_export_user,
        exporter=exporter,
        exporter_office=exporter_office,
        status=ImpExpStatus.PROCESSING,
        reference="GMP/2022/12345",
    )

    app.countries.add(Country.objects.get(name="Finland"))
    app.countries.add(Country.objects.get(name="Germany"))

    GMPBrand.objects.create(application=app, brand_name="Brand 1")
    GMPBrand.objects.create(application=app, brand_name="Brand 2")
    GMPBrand.objects.create(application=app, brand_name="Brand 3")

    document_pack.pack_draft_create(app)

    return app
