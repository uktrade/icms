import pytest

from web.domains.case.shared import ImpExpStatus
from web.models import (
    CertificateOfManufactureApplication,
    ExportApplicationType,
    ImportApplicationType,
    SILApplication,
)


@pytest.fixture
def fa_sil_app(db, importer_one_main_contact, importer, office):
    """Fake FA-SIL app to test permission code.

    This application is in PROCESSING state.
    """

    app = SILApplication.objects.create(
        process_type=SILApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type="FA", sub_type="SIL"),
        created_by=importer_one_main_contact,
        last_updated_by=importer_one_main_contact,
        importer=importer,
        importer_office=office,
        status=ImpExpStatus.PROCESSING,
        reference="IMI/2022/12345",
    )

    return app


@pytest.fixture
def fa_sil_agent_app(
    importer, office, agent_importer, importer_one_agent_office, importer_one_agent_one_contact
):
    app = SILApplication.objects.create(
        process_type=SILApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(type="FA", sub_type="SIL"),
        created_by=importer_one_agent_one_contact,
        last_updated_by=importer_one_agent_one_contact,
        importer=importer,
        importer_office=office,
        agent=agent_importer,
        agent_office=importer_one_agent_office,
        status=ImpExpStatus.PROCESSING,
        reference="IMI/2022/12346",
    )

    return app


@pytest.fixture
def com_app(db, exporter, exporter_office, exporter_one_main_contact):
    """Fake COM app to test permission code.

    This application is in PROCESSING state.
    """

    app = CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code="CFS"),
        created_by=exporter_one_main_contact,
        last_updated_by=exporter_one_main_contact,
        exporter=exporter,
        exporter_office=exporter_office,
        status=ImpExpStatus.PROCESSING,
        reference="COM/2022/12345",
    )

    return app


@pytest.fixture
def com_agent_app(
    exporter,
    exporter_office,
    agent_exporter,
    exporter_one_agent_one_office,
    exporter_one_agent_one_contact,
):
    """Fake COM app to test permission code.

    This application is in PROCESSING state.
    """

    app = CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(type_code="CFS"),
        created_by=exporter_one_agent_one_contact,
        last_updated_by=exporter_one_agent_one_contact,
        exporter=exporter,
        exporter_office=exporter_office,
        agent=agent_exporter,
        agent_office=exporter_one_agent_one_office,
        status=ImpExpStatus.PROCESSING,
        reference="COM/2022/12346",
    )

    return app
