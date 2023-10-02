from unittest.mock import Mock

import pytest

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.models import (
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    Country,
    ExportApplicationType,
    ImportApplicationType,
    SanctionsAndAdhocApplication,
    SILApplication,
)


@pytest.fixture
def lock_manager():
    return Mock()


@pytest.fixture
def fa_sil(db, importer_one_contact, importer, office):
    """Fake FA-SIL app to test document pack service.

    This application is in PROCESSING state.
    """

    app = SILApplication.objects.create(
        process_type=SILApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type="FA", sub_type="SIL"),
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
        importer=importer,
        importer_office=office,
        status=ImpExpStatus.PROCESSING,
        reference="IMI/2022/12345",
    )

    return app


@pytest.fixture
def com(db, exporter_one_contact, exporter, exporter_office):
    """Fake COM app to test document pack service.

    This application is in PROCESSING state.
    """

    app = CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code="CFS"),
        created_by=exporter_one_contact,
        last_updated_by=exporter_one_contact,
        exporter=exporter,
        exporter_office=exporter_office,
        status=ImpExpStatus.PROCESSING,
        reference="COM/2022/12345",
    )

    return app


@pytest.fixture
def sanctions(db, importer_one_contact, importer, office):
    """Fake ADHOC app to test document pack service.

    This application is in PROCESSING state.
    """

    app = SanctionsAndAdhocApplication.objects.create(
        process_type=SanctionsAndAdhocApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type="ADHOC"),
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
        importer=importer,
        importer_office=office,
        status=ImpExpStatus.PROCESSING,
        reference="IMI/2022/12346",
    )

    return app


@pytest.fixture
def iar(importer_access_request):
    """Fixture just to shorten name"""
    return importer_access_request


@pytest.fixture
def fa_sil_with_draft(fa_sil):
    document_pack.pack_draft_create(fa_sil)

    return fa_sil


@pytest.fixture
def sanctions_with_draft(sanctions):
    document_pack.pack_draft_create(sanctions)

    return sanctions


@pytest.fixture
def com_with_draft(com):
    document_pack.pack_draft_create(com)

    com.countries.add(Country.objects.get(name="Finland"))
    com.countries.add(Country.objects.get(name="Germany"))

    return com


@pytest.fixture
def gmp_with_draft(db, exporter_one_contact, exporter, exporter_office):
    """Fake COM app to test document pack service.

    This application is in PROCESSING state.
    """

    app = CertificateOfGoodManufacturingPracticeApplication.objects.create(
        process_type=CertificateOfGoodManufacturingPracticeApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code="GMP"),
        created_by=exporter_one_contact,
        last_updated_by=exporter_one_contact,
        exporter=exporter,
        exporter_office=exporter_office,
        status=ImpExpStatus.PROCESSING,
        reference="GMP/2022/12345",
    )

    app.countries.add(Country.objects.get(name="Finland"))
    app.countries.add(Country.objects.get(name="Germany"))

    document_pack.pack_draft_create(app)

    return app
