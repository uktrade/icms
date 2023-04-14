import pytest

from web.models import AccessRequest, Task
from web.tests.domains.case.access.factories import (
    ExporterAccessRequestFactory,
    ImporterAccessRequestFactory,
)


@pytest.mark.django_db
def test_exporter_management_access_approval_ok(exporter_client, icms_admin_client):
    response = exporter_client.get("/access/case/3/exporter/approval-request/")

    assert response.status_code == 403

    access_request = ExporterAccessRequestFactory.create(
        status=AccessRequest.Statuses.SUBMITTED, link=None
    )
    Task.objects.create(process=access_request, task_type=Task.TaskType.PROCESS)

    response = icms_admin_client.get(f"/access/case/{access_request.pk}/exporter/approval-request/")

    assert response.status_code == 200
    assert "Exporter Access Approval" in response.content.decode()


@pytest.mark.django_db
def test_importer_management_access_approval_ok(importer_client, icms_admin_client):
    response = importer_client.get("/access/case/3/importer/approval-request/")
    assert response.status_code == 403

    access_request = ImporterAccessRequestFactory.create(
        status=AccessRequest.Statuses.SUBMITTED, link=None
    )
    Task.objects.create(process=access_request, task_type=Task.TaskType.PROCESS)

    response = icms_admin_client.get(f"/access/case/{access_request.pk}/importer/approval-request/")

    assert response.status_code == 200
    assert "Importer Access Approval" in response.content.decode()
