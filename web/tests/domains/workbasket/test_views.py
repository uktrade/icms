import re

import pytest

from web.models import (
    CertificateOfManufactureApplication,
    ExportApplication,
    ExportApplicationType,
    ImportApplication,
    ImportApplicationType,
    OpenIndividualLicenceApplication,
)
from web.tests.helpers import get_test_client


@pytest.fixture
def submitted_imp_appl(importer, importer_one_contact):
    return OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            sub_type=ImportApplicationType.SubTypes.OIL
        ),
        status=ImportApplication.Statuses.SUBMITTED,
        importer=importer,
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
    )


@pytest.fixture
def in_progress_imp_appl(importer, importer_one_contact):
    return OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            sub_type=ImportApplicationType.SubTypes.OIL
        ),
        status=ImportApplication.Statuses.IN_PROGRESS,
        importer=importer,
        created_by=importer_one_contact,
        last_updated_by=importer_one_contact,
    )


@pytest.fixture
def submitted_exp_appl(exporter, exporter_one_contact):
    return CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.MANUFACTURE
        ),
        status=ExportApplication.Statuses.SUBMITTED,
        exporter=exporter,
        created_by=exporter_one_contact,
        last_updated_by=exporter_one_contact,
    )


@pytest.fixture
def in_progress_exp_appl(exporter, exporter_one_contact):
    return CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.MANUFACTURE
        ),
        status=ExportApplication.Statuses.IN_PROGRESS,
        exporter=exporter,
        created_by=exporter_one_contact,
        last_updated_by=exporter_one_contact,
    )


@pytest.fixture
def submitted_agent_imp_appl(importer, agent_importer, importer_one_agent_one_contact):
    return OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            sub_type=ImportApplicationType.SubTypes.OIL
        ),
        status=ImportApplication.Statuses.SUBMITTED,
        importer=importer,
        created_by=importer_one_agent_one_contact,
        last_updated_by=importer_one_agent_one_contact,
        agent=agent_importer,
    )


@pytest.fixture
def in_progress_agent_imp_appl(importer, agent_importer, importer_one_agent_one_contact):
    return OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            sub_type=ImportApplicationType.SubTypes.OIL
        ),
        status=ImportApplication.Statuses.IN_PROGRESS,
        importer=importer,
        created_by=importer_one_agent_one_contact,
        last_updated_by=importer_one_agent_one_contact,
        agent=agent_importer,
    )


@pytest.mark.django_db
def test_importer_workbasket(
    importer_client,
    in_progress_imp_appl,
    submitted_imp_appl,
    in_progress_exp_appl,
    submitted_exp_appl,
    in_progress_agent_imp_appl,
    submitted_agent_imp_appl,
    complete_rejected_app,
):
    response = importer_client.get("/workbasket/")
    assert response.status_code == 200

    html = response.content.decode()

    assert '<div class="result-count">3 workbasket items</div>' in html

    _check_in_progress_workbasket(in_progress_imp_appl, html)
    _check_submitted_workbasket(submitted_imp_appl, html)
    _check_refused_workbasket(complete_rejected_app, html)


@pytest.mark.django_db
def test_exporter_workbasket(
    exporter_client,
    in_progress_imp_appl,
    submitted_imp_appl,
    in_progress_exp_appl,
    submitted_exp_appl,
    in_progress_agent_imp_appl,
    submitted_agent_imp_appl,
    complete_rejected_export_app,
):
    response = exporter_client.get("/workbasket/")

    assert response.status_code == 200

    html = response.content.decode()
    assert '<div class="result-count">3 workbasket items</div>' in html

    _check_in_progress_workbasket(in_progress_exp_appl, html)
    _check_submitted_workbasket(submitted_exp_appl, html)
    _check_refused_workbasket(complete_rejected_export_app, html)


@pytest.mark.django_db
def test_agent_import_workbasket(
    importer_one_agent_one_contact,
    in_progress_imp_appl,
    submitted_imp_appl,
    in_progress_exp_appl,
    submitted_exp_appl,
    in_progress_agent_imp_appl,
    submitted_agent_imp_appl,
):
    client = get_test_client(importer_one_agent_one_contact)
    response = client.get("/workbasket/")

    assert response.status_code == 200

    html = response.content.decode()
    assert '<div class="result-count">2 workbasket items</div>' in html

    _check_in_progress_workbasket(in_progress_agent_imp_appl, html)
    _check_submitted_workbasket(submitted_agent_imp_appl, html)


@pytest.mark.django_db
def test_refused_apps_excluded_from_admin_workbasket(
    ilb_admin_client, complete_rejected_app, complete_rejected_export_app
):
    response = ilb_admin_client.get("/workbasket/")
    assert response.status_code == 200
    html = response.content.decode()
    assert '<div class="result-count">2 workbasket items</div>' in html


def _check_in_progress_workbasket(appl, html):
    link = rf'<a href=".*/{appl.pk}/edit/">\s*Resume\s*</a>'
    assert re.search(link, html) is not None


def _check_submitted_workbasket(appl, html):
    link = rf'<a href=".*/{appl.pk}/view/">\s*View Application\s*</a>'
    assert re.search(link, html) is not None


def _check_refused_workbasket(appl, html):
    assert "Completed (Refused)" in html
    _check_submitted_workbasket(appl, html)
