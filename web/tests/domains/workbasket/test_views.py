import re

import pytest
from django.test import Client
from guardian.shortcuts import assign_perm

from web.domains.case._import.fa_oil.models import OpenIndividualLicenceApplication
from web.domains.case._import.models import ImportApplication
from web.domains.importer.models import Importer
from web.flow.models import Task
from web.tests.domains.case._import.factory import OILApplicationFactory
from web.tests.domains.importer.factory import ImporterFactory
from web.tests.domains.user.factory import ActiveUserFactory


@pytest.mark.django_db
def test_resume_oil_application():
    user = ActiveUserFactory.create(permission_codenames=["importer_access"])
    importer = ImporterFactory.create(type=Importer.ORGANISATION, user=user)
    assign_perm("web.is_contact_of_importer", user, importer)

    in_progress = OILApplicationFactory.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        is_active=True,
        created_by=user,
        last_updated_by=user,
        importer=importer,
        status=ImportApplication.IN_PROGRESS,
    )
    Task.objects.create(process=in_progress, task_type="prepare", owner=user)

    submitted = OILApplicationFactory.create(
        process_type=OpenIndividualLicenceApplication.PROCESS_TYPE,
        is_active=True,
        created_by=user,
        last_updated_by=user,
        importer=importer,
        status=ImportApplication.SUBMITTED,
    )
    Task.objects.create(process=submitted, task_type="prepare", owner=user)

    client = Client()
    client.login(username=user.username, password="test")
    response = client.get("/workbasket/")

    assert response.status_code == 200

    link = r'<a href="/import/firearms/oil/\d+/edit/">\s*Resume\s*</a>'
    assert re.search(link, response.content.decode()) is not None
