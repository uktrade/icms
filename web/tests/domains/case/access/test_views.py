import pytest

from web.tests.domains.case.access.factories import (
    ExporterAccessRequestFactory,
    ImporterAccessRequestFactory,
)


@pytest.mark.django_db
def test_list_importer_access_request_ok(importer_client, ilb_admin_client):
    response = importer_client.get("/access/importer/")
    assert response.status_code == 403

    ImporterAccessRequestFactory.create()
    response = ilb_admin_client.get("/access/importer/")

    assert response.status_code == 200
    assert "Search Importer Access Requests" in response.content.decode()


@pytest.mark.django_db
def test_list_exporter_access_request_ok(exporter_client, ilb_admin_client):
    response = exporter_client.get("/access/exporter/")

    assert response.status_code == 403

    ExporterAccessRequestFactory.create()
    response = ilb_admin_client.get("/access/exporter/")

    assert response.status_code == 200
    assert "Search Exporter Access Requests" in response.content.decode()
