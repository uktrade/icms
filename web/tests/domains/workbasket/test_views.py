import re

import pytest
from django.test import Client

from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
from web.domains.case._import.models import ImportApplication, ImportApplicationType
from web.domains.case.export.models import (
    CertificateOfManufactureApplication,
    ExportApplication,
    ExportApplicationType,
)


@pytest.fixture
def submitted_imp_appl(importer, test_import_user):
    return OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            sub_type=ImportApplicationType.SubTypes.OIL
        ),
        status=ImportApplication.Statuses.SUBMITTED,
        importer=importer,
        created_by=test_import_user,
        last_updated_by=test_import_user,
    )


@pytest.fixture
def in_progress_imp_appl(importer, test_import_user):
    return OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            sub_type=ImportApplicationType.SubTypes.OIL
        ),
        status=ImportApplication.Statuses.IN_PROGRESS,
        importer=importer,
        created_by=test_import_user,
        last_updated_by=test_import_user,
    )


@pytest.fixture
def submitted_exp_appl(exporter, test_export_user):
    return CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.MANUFACTURE
        ),
        status=ExportApplication.Statuses.SUBMITTED,
        exporter=exporter,
        created_by=test_export_user,
        last_updated_by=test_export_user,
    )


@pytest.fixture
def in_progress_exp_appl(exporter, test_export_user):
    return CertificateOfManufactureApplication.objects.create(
        process_type=CertificateOfManufactureApplication.PROCESS_TYPE,
        application_type=ExportApplicationType.objects.get(
            type_code=ExportApplicationType.Types.MANUFACTURE
        ),
        status=ExportApplication.Statuses.IN_PROGRESS,
        exporter=exporter,
        created_by=test_export_user,
        last_updated_by=test_export_user,
    )


@pytest.fixture
def submitted_agent_imp_appl(importer, agent_importer, test_agent_import_user):
    return OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            sub_type=ImportApplicationType.SubTypes.OIL
        ),
        status=ImportApplication.Statuses.SUBMITTED,
        importer=importer,
        created_by=test_agent_import_user,
        last_updated_by=test_agent_import_user,
        agent=agent_importer,
    )


@pytest.fixture
def in_progress_agent_imp_appl(importer, agent_importer, test_agent_import_user):
    return OpenIndividualLicenceApplication.objects.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        application_type=ImportApplicationType.objects.get(
            sub_type=ImportApplicationType.SubTypes.OIL
        ),
        status=ImportApplication.Statuses.IN_PROGRESS,
        importer=importer,
        created_by=test_agent_import_user,
        last_updated_by=test_agent_import_user,
        agent=agent_importer,
    )


@pytest.mark.django_db
def test_importer_workbasket(
    test_import_user,
    in_progress_imp_appl,
    submitted_imp_appl,
    in_progress_exp_appl,
    submitted_exp_appl,
    in_progress_agent_imp_appl,
    submitted_agent_imp_appl,
):
    client = Client()
    client.login(username=test_import_user.username, password="test")
    response = client.get("/workbasket/")

    assert response.status_code == 200

    html = response.content.decode()
    assert '<div class="result-count">2 workbasket items</div>' in html

    _check_in_progress_workbasket(in_progress_imp_appl, html)
    _check_submitted_workbasket(submitted_imp_appl, html)


@pytest.mark.django_db
def test_exporter_workbasket(
    test_export_user,
    in_progress_imp_appl,
    submitted_imp_appl,
    in_progress_exp_appl,
    submitted_exp_appl,
    in_progress_agent_imp_appl,
    submitted_agent_imp_appl,
):
    client = Client()
    client.login(username=test_export_user.username, password="test")
    response = client.get("/workbasket/")

    assert response.status_code == 200

    html = response.content.decode()
    assert '<div class="result-count">2 workbasket items</div>' in html

    _check_in_progress_workbasket(in_progress_exp_appl, html)
    _check_submitted_workbasket(submitted_exp_appl, html)


@pytest.mark.django_db
def test_agent_import_workbasket(
    test_agent_import_user,
    in_progress_imp_appl,
    submitted_imp_appl,
    in_progress_exp_appl,
    submitted_exp_appl,
    in_progress_agent_imp_appl,
    submitted_agent_imp_appl,
):
    client = Client()
    client.login(username=test_agent_import_user.username, password="test")
    response = client.get("/workbasket/")

    assert response.status_code == 200

    html = response.content.decode()
    assert '<div class="result-count">2 workbasket items</div>' in html

    _check_in_progress_workbasket(in_progress_agent_imp_appl, html)
    _check_submitted_workbasket(submitted_agent_imp_appl, html)


def _check_in_progress_workbasket(appl, html):
    link = rf'<a href=".*/{appl.pk}/edit/">\s*Resume\s*</a>'
    assert re.search(link, html) is not None


def _check_submitted_workbasket(appl, html):
    link = rf'<a href=".*/{appl.pk}/view/">\s*View\s*</a>'
    assert re.search(link, html) is not None
