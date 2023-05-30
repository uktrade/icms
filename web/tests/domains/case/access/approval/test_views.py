def test_exporter_management_access_approval_ok(
    exporter_client, ilb_admin_client, exporter_access_request
):
    response = exporter_client.get("/access/case/3/exporter/approval-request/")

    assert response.status_code == 403

    access_request = exporter_access_request

    response = ilb_admin_client.get(f"/access/case/{access_request.pk}/exporter/approval-request/")

    assert response.status_code == 200
    assert "Exporter Access Approval" in response.content.decode()


def test_importer_management_access_approval_ok(
    importer_client, ilb_admin_client, importer_access_request
):
    response = importer_client.get("/access/case/3/importer/approval-request/")
    assert response.status_code == 403

    access_request = importer_access_request

    response = ilb_admin_client.get(f"/access/case/{access_request.pk}/importer/approval-request/")

    assert response.status_code == 200
    assert "Importer Access Approval" in response.content.decode()
