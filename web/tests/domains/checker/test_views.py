from http import HTTPStatus
from unittest.mock import patch

from django.urls import reverse

from web.domains.case.services import document_pack
from web.models import File


def _add_dummy_document(document_reference):
    doc = File.objects.create(
        path="dummy-path",
        filename="dummy-filename",
        content_type="application/pdf",
        file_size=100,
        created_by_id=0,
    )
    document_reference.document = doc
    document_reference.save()


def test_caseworker_domain_no_access(cw_client):
    url = reverse("checker:certificate-checker")
    response = cw_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_importer_domain_no_access(imp_client):
    url = reverse("checker:certificate-checker")
    response = imp_client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_prepopulate_form(exp_client):
    url = (
        reverse("checker:certificate-checker") + "?CERTIFICATE_CODE=1234&CERTIFICATE_REFERENCE=5678"
    )
    response = exp_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert (
        '<input id="id_certificate_reference" maxlength="16" name="certificate_reference" required="" type="text" value="5678"/>'
        in str(response.content)
    )
    assert (
        '<input id="id_certificate_code" maxlength="16" name="certificate_code" required="" type="text" value="1234"/>'
        in str(response.content)
    )


def test_no_certificate_code(exp_client):
    post_data = {
        "certificate_reference": "1234",
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK
    assert "You must enter a certificate reference and code." in str(response.content)


def test_unknown_certificate_code(exp_client, completed_cfs_app):
    cert = document_pack.pack_latest_get(completed_cfs_app)
    doc = cert.document_references.first()

    post_data = {"certificate_reference": doc.reference, "certificate_code": "abcd"}
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK

    assert (
        f"Certificate {doc.reference} could not be found with the given code abcd. Please ensure the reference and code is entered correctly and try again."
        in str(response.content)
    )


def test_no_certificate_reference(exp_client):
    post_data = {"certificate_code": "1234"}
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK
    assert "You must enter a certificate reference and code." in str(response.content)


def test_unknown_certificate_reference(exp_client, completed_cfs_app):
    cert = document_pack.pack_latest_get(completed_cfs_app)
    doc = cert.document_references.first()

    post_data = {"certificate_reference": "1234", "certificate_code": doc.check_code}
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK

    assert (
        f"Certificate 1234 could not be found with the given code {doc.check_code}. Please ensure the reference and code is entered correctly and try again."
        in str(response.content)
    )


@patch("web.domains.checker.views.create_presigned_url")
def test_check_cfs_certifcate(mock_presign_url, exp_client, completed_cfs_app):
    mock_presign_url.return_value = ""
    cert = document_pack.pack_latest_get(completed_cfs_app)
    doc = cert.document_references.first()
    _add_dummy_document(doc)

    post_data = {"certificate_reference": doc.reference, "certificate_code": doc.check_code}
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)
    content = str(response.content)
    issue_date = cert.case_completion_datetime.strftime("%d %B %Y")

    assert response.status_code == HTTPStatus.OK
    assert f"Certificate {doc.reference} is valid." in content
    assert f'<td id="certificate-reference">{doc.reference}</td>' in content
    assert '<td id="certificate-exporter-name">Test Exporter 1</td>' in content
    assert '<td id="certificate-country">Afghanistan</td>' in content
    assert '<td id="certificate-goods">A Product</td>' in content
    assert f'<td id="certificate-issue-date">{issue_date}</td>' in content
    assert '<td id="certificate-status">Valid</td>' in content


@patch("web.domains.checker.views.create_presigned_url")
def test_check_gmp_certifcate(mock_presign_url, exp_client, completed_gmp_app):
    app = completed_gmp_app
    mock_presign_url.return_value = ""
    cert = document_pack.pack_latest_get(app)
    doc = cert.document_references.first()
    _add_dummy_document(doc)

    post_data = {"certificate_reference": doc.reference, "certificate_code": doc.check_code}
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)
    content = str(response.content)
    issue_date = cert.case_completion_datetime.strftime("%d %B %Y")

    assert response.status_code == HTTPStatus.OK
    assert f"Certificate {doc.reference} is valid." in content
    assert f'<td id="certificate-reference">{doc.reference}</td>' in content
    assert '<td id="certificate-exporter-name">Test Exporter 1</td>' in content
    assert '<td id="certificate-country">China</td>' in content
    assert '<td id="certificate-goods">N/A</td>' in content
    assert f'<td id="certificate-issue-date">{issue_date}</td>' in content
    assert '<td id="certificate-status">Valid</td>' in content


@patch("web.domains.checker.views.create_presigned_url")
def test_check_com_certifcate(mock_presign_url, exp_client, completed_com_app):
    app = completed_com_app
    mock_presign_url.return_value = ""
    cert = document_pack.pack_latest_get(app)
    doc = cert.document_references.first()
    _add_dummy_document(doc)

    post_data = {"certificate_reference": doc.reference, "certificate_code": doc.check_code}
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)
    content = str(response.content)
    issue_date = cert.case_completion_datetime.strftime("%d %B %Y")

    assert response.status_code == HTTPStatus.OK
    assert f"Certificate {doc.reference} is valid." in content
    assert f'<td id="certificate-reference">{doc.reference}</td>' in content
    assert '<td id="certificate-exporter-name">Test Exporter 1</td>' in content
    assert '<td id="certificate-country">Afghanistan</td>' in content
    assert f'<td id="certificate-goods">{app.product_name}</td>' in content
    assert f'<td id="certificate-issue-date">{issue_date}</td>' in content
    assert '<td id="certificate-status">Valid</td>' in content


@patch("web.domains.checker.views.create_presigned_url")
def test_check_cfs_revoked_certifcate(mock_presign_url, exp_client, completed_cfs_app):
    app = completed_cfs_app
    mock_presign_url.return_value = ""
    document_pack.pack_active_revoke(app, "TEST", True)
    cert = document_pack.pack_revoked_get(app)
    doc = cert.document_references.first()
    _add_dummy_document(doc)

    post_data = {"certificate_reference": doc.reference, "certificate_code": doc.check_code}
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)
    content = str(response.content)
    issue_date = cert.case_completion_datetime.strftime("%d %B %Y")

    assert response.status_code == HTTPStatus.OK
    assert f"Certificate {doc.reference} is valid." in content
    assert f'<td id="certificate-reference">{doc.reference}</td>' in content
    assert '<td id="certificate-exporter-name">Test Exporter 1</td>' in content
    assert '<td id="certificate-country">Afghanistan</td>' in content
    assert '<td id="certificate-goods">A Product</td>' in content
    assert f'<td id="certificate-issue-date">{issue_date}</td>' in content
    assert '<td id="certificate-status">Revoked</td>' in content
