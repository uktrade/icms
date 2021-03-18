import pytest
from django.test import Client

from web.domains.importer.models import Importer
from web.tests.domains.importer import factory as importer_factories
from web.tests.domains.user import factory as user_factories
from web.tests.flow import factories as process_factories

from . import factory


@pytest.mark.django_db
def test_preview_cover_letter():
    ilb_admin = user_factories.ActiveUserFactory.create(
        permission_codenames=["reference_data_access"]
    )
    user = user_factories.ActiveUserFactory.create(permission_codenames=["importer_access"])
    importer = importer_factories.ImporterFactory.create(type=Importer.ORGANISATION, user=user)

    process = factory.OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        created_by=user,
        last_updated_by=user,
        case_owner=ilb_admin,
    )
    process_factories.TaskFactory.create(process=process, task_type="process")

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    response = client.get(f"/import/case/{process.pk}/cover-letter/preview/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=CoverLetter.pdf"

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 20000 < len(pdf) < 30000


@pytest.mark.django_db
def test_preview_licence():
    ilb_admin = user_factories.ActiveUserFactory.create(
        permission_codenames=["reference_data_access"]
    )
    user = user_factories.ActiveUserFactory.create(permission_codenames=["importer_access"])
    importer = importer_factories.ImporterFactory.create(type=Importer.ORGANISATION, user=user)

    process = factory.OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        created_by=user,
        last_updated_by=user,
        case_owner=ilb_admin,
    )
    process_factories.TaskFactory.create(process=process, task_type="process")

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    response = client.get(f"/import/case/{process.pk}/licence/preview/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=Licence.pdf"

    pdf = response.content
    assert pdf.startswith(b"%PDF-")
    # ensure the pdf generated has some content
    assert 20000 < len(pdf) < 30000
