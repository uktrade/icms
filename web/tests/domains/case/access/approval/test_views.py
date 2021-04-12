import pytest
from django.test import Client

from web.domains.case.access.models import AccessRequest
from web.flow.models import Task
from web.tests.domains.case.access.factories import (
    ExporterAccessRequestFactory,
    ImporterAccessRequestFactory,
)
from web.tests.domains.user.factory import ActiveUserFactory


@pytest.mark.django_db
def test_exporter_management_access_approval_ok():
    client = Client()

    user = ActiveUserFactory.create()
    client.login(username=user.username, password="test")
    response = client.get("/access/case/3/exporter/approval-request/")

    assert response.status_code == 403

    ilb_admin = ActiveUserFactory.create(permission_codenames=["reference_data_access"])
    access_request = ExporterAccessRequestFactory.create(status=AccessRequest.SUBMITTED, link=None)
    Task.objects.create(process=access_request, task_type="process")

    client.login(username=ilb_admin.username, password="test")
    response = client.get(f"/access/case/{access_request.pk}/exporter/approval-request/")

    assert response.status_code == 200
    assert "Exporter Access Approval" in response.content.decode()


@pytest.mark.django_db
def test_importer_management_access_approval_ok():
    client = Client()

    user = ActiveUserFactory.create()
    client.login(username=user.username, password="test")
    response = client.get("/access/case/3/importer/approval-request/")

    assert response.status_code == 403

    ilb_admin = ActiveUserFactory.create(permission_codenames=["reference_data_access"])
    access_request = ImporterAccessRequestFactory.create(status=AccessRequest.SUBMITTED, link=None)
    Task.objects.create(process=access_request, task_type="process")

    client.login(username=ilb_admin.username, password="test")
    response = client.get(f"/access/case/{access_request.pk}/importer/approval-request/")

    assert response.status_code == 200
    assert "Importer Access Approval" in response.content.decode()
