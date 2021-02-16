import pytest
from django.test import Client

from web.domains.case._import.firearms.models import ChecklistFirearmsOILApplication
from web.domains.importer.models import Importer
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import ActiveUserFactory
from web.tests.flow.factories import TaskFactory

from .. import factory


@pytest.mark.django_db
def test_manage_checklist():
    ilb_admin = ActiveUserFactory.create(permission_codenames=["reference_data_access"])
    user = ActiveUserFactory.create(permission_codenames=["importer_access"])
    importer = ImporterFactory.create(type=Importer.ORGANISATION, user=user)

    process = factory.OILApplicationFactory.create(
        status="SUBMITTED",
        importer=importer,
        created_by=user,
        last_updated_by=user,
        case_owner=ilb_admin,
    )
    TaskFactory.create(process=process, task_type="process")

    client = Client()
    client.login(username=ilb_admin.username, password="test")
    path = f"/import/firearms/case/oil/{process.pk}/checklist/"
    response = client.get(path)
    assert response.status_code == 200
    assert process.checklists.count() == 1

    client.post(path, data={"authorisation": "on"}, follow=True)
    assert response.status_code == 200
    checklist = ChecklistFirearmsOILApplication.objects.get()
    assert checklist.authorisation is True
    assert process.checklists.count() == 1
