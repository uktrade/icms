from http import HTTPStatus
from unittest.mock import patch

import pytest
from django.urls import reverse

from web.domains.case.services import document_pack
from web.domains.checker.views import _get_export_application_goods
from web.models import CFSProduct, CFSSchedule, Country, File


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


def test_get_export_application_goods_gmp(completed_gmp_app):
    assert _get_export_application_goods(completed_gmp_app) == "N/A"


def test_get_export_application_goods_com(completed_com_app):
    assert _get_export_application_goods(completed_com_app) == "Example product name"


def test_get_export_application_goods_cfs(completed_cfs_app, exporter_one_contact):
    assert _get_export_application_goods(completed_cfs_app) == "A Product"

    # Add another schedule and more products
    schedule = CFSSchedule.objects.create(
        application=completed_cfs_app, created_by=exporter_one_contact
    )

    CFSProduct.objects.create(schedule=schedule, product_name="New Product")
    CFSProduct.objects.create(schedule=schedule, product_name="Test Product")

    assert (
        _get_export_application_goods(completed_cfs_app) == "A Product, New Product, Test Product"
    )


def test_get_export_application_goods_invalid(completed_sil_app):
    with pytest.raises(ValueError, match="not an ExportApplication process type."):
        _get_export_application_goods(completed_sil_app)


def test_caseworker_domain_no_access(cw_client):
    url = reverse("checker:certificate-checker")
    response = cw_client.get(url)

    # Allowed for now (as we don't know what site the redirect will point to)
    assert response.status_code == HTTPStatus.OK


def test_importer_domain_no_access(imp_client):
    url = reverse("checker:certificate-checker")
    response = imp_client.get(url)

    # Allowed for now (as we don't know what site the redirect will point to)
    assert response.status_code == HTTPStatus.OK


def test_prepopulate_form(exp_client):
    country = Country.objects.first()
    url = (
        reverse("checker:certificate-checker")
        + f"?CERTIFICATE_CODE=1234&CERTIFICATE_REFERENCE=5678&COUNTRY={country.id}&ORGANISATION=TEST%20EXPORTER"
    )
    response = exp_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert (
        '<input id="id_certificate_reference" maxlength="16" name="certificate_reference" required="" type="text" value="5678"/>'
        in str(response.content)
    )
    assert f'<option selected="" value="{country.id}">{country.name}</option>' in str(
        response.content
    )

    assert (
        '<input id="id_organisation_name" maxlength="255" name="organisation_name" required="" type="text" value="TEST EXPORTER"/>'
        in str(response.content)
    )


def test_no_certificate_code(exp_client):
    post_data = {
        "certificate_reference": "1234",
        "country": 1,
        "organisation_name": "Test Exporter",
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK
    assert "You must enter all details" in str(response.content)


def test_unknown_certificate_code(exp_client, completed_cfs_app):
    app = completed_cfs_app
    cert = document_pack.pack_latest_get(completed_cfs_app)
    doc = cert.document_references.first()

    post_data = {
        "certificate_reference": doc.reference,
        "certificate_code": "abcd",
        "country": doc.reference_data.country_id,
        "organisation_name": app.exporter.name,
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK

    assert (
        f"Certificate {doc.reference} could not be found with the given code abcd. Please ensure all details are entered correctly and try again."
        in str(response.content)
    )


def test_no_certificate_reference(exp_client):
    post_data = {
        "certificate_code": "1234",
        "country": 1,
        "organisation_name": "Test Exporter",
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK
    assert "You must enter all details" in str(response.content)


def test_unknown_certificate_reference(exp_client, completed_cfs_app):
    app = completed_cfs_app
    cert = document_pack.pack_latest_get(completed_cfs_app)
    doc = cert.document_references.first()

    post_data = {
        "certificate_reference": "1234",
        "certificate_code": doc.check_code,
        "country": doc.reference_data.country_id,
        "organisation_name": app.exporter.name,
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK

    assert (
        f"Certificate 1234 could not be found with the given code {doc.check_code}. Please ensure all details are entered correctly and try again."
        in str(response.content)
    )


def test_no_country(exp_client, completed_cfs_app):
    app = completed_cfs_app
    cert = document_pack.pack_latest_get(completed_cfs_app)
    doc = cert.document_references.first()

    post_data = {
        "certificate_reference": doc.reference,
        "certificate_code": doc.check_code,
        "organisation_name": app.exporter.name,
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK
    assert "You must enter all details" in str(response.content)


def test_unknown_country(exp_client, completed_cfs_app):
    app = completed_cfs_app
    cert = document_pack.pack_latest_get(completed_cfs_app)
    doc = cert.document_references.first()

    post_data = {
        "certificate_reference": doc.reference,
        "certificate_code": doc.check_code,
        "country": 9999,
        "organisation_name": app.exporter.name,
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK
    assert "You must enter all details" in str(response.content)


def test_no_exporter(exp_client, completed_cfs_app):
    cert = document_pack.pack_latest_get(completed_cfs_app)
    doc = cert.document_references.first()

    post_data = {
        "certificate_reference": doc.reference,
        "certificate_code": doc.check_code,
        "country": doc.reference_data.country_id,
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK
    assert "You must enter all details" in str(response.content)


def test_unknown_exporter(exp_client, completed_cfs_app):
    cert = document_pack.pack_latest_get(completed_cfs_app)
    doc = cert.document_references.first()

    post_data = {
        "certificate_reference": doc.reference,
        "certificate_code": doc.check_code,
        "country": doc.reference_data.country_id,
        "organisation_name": "some-link",
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)

    assert response.status_code == HTTPStatus.OK

    assert (
        f"Certificate {doc.reference} could not be found with the given code {doc.check_code}. Please ensure all details are entered correctly and try again."
        in str(response.content)
    )


@patch("web.domains.checker.views.create_presigned_url")
def test_check_cfs_certifcate(mock_presign_url, exp_client, completed_cfs_app):
    mock_presign_url.return_value = "some-link"
    app = completed_cfs_app
    cert = document_pack.pack_latest_get(completed_cfs_app)
    doc = cert.document_references.first()
    _add_dummy_document(doc)

    post_data = {
        "certificate_reference": doc.reference,
        "certificate_code": doc.check_code,
        "country": doc.reference_data.country_id,
        "organisation_name": app.exporter.name,
    }
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
    assert (
        '<td id="certificate-document"><a href="some-link" style="display: block">Download</a></td>'
        in content
    )


@patch("web.domains.checker.views.create_presigned_url")
def test_check_gmp_certifcate(mock_presign_url, exp_client, completed_gmp_app):
    app = completed_gmp_app
    mock_presign_url.return_value = "some-link"
    cert = document_pack.pack_latest_get(app)
    doc = cert.document_references.first()
    _add_dummy_document(doc)

    post_data = {
        "certificate_reference": doc.reference,
        "certificate_code": doc.check_code,
        "country": doc.reference_data.country_id,
        "organisation_name": app.manufacturer_name,
    }
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
    assert (
        '<td id="certificate-document"><a href="some-link" style="display: block">Download</a></td>'
        in content
    )


@patch("web.domains.checker.views.create_presigned_url")
def test_check_com_certifcate(mock_presign_url, exp_client, completed_com_app):
    app = completed_com_app
    mock_presign_url.return_value = "some-link"
    cert = document_pack.pack_latest_get(app)
    doc = cert.document_references.first()
    _add_dummy_document(doc)

    post_data = {
        "certificate_reference": doc.reference,
        "certificate_code": doc.check_code,
        "country": doc.reference_data.country_id,
        "organisation_name": app.exporter.name,
    }
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
    assert (
        '<td id="certificate-document"><a href="some-link" style="display: block">Download</a></td>'
        in content
    )


@patch("web.domains.checker.views.create_presigned_url")
def test_check_download_link_fail(mock_presign_url, exp_client, completed_com_app):
    app = completed_com_app
    mock_presign_url.return_value = None
    cert = document_pack.pack_latest_get(app)
    doc = cert.document_references.first()
    _add_dummy_document(doc)

    post_data = {
        "certificate_reference": doc.reference,
        "certificate_code": doc.check_code,
        "country": doc.reference_data.country_id,
        "organisation_name": app.exporter.name,
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)
    content = str(response.content)
    issue_date = cert.case_completion_datetime.strftime("%d %B %Y")

    assert response.status_code == HTTPStatus.OK
    assert "A download link failed to generate. Please resubmit the form." in content
    assert f'<td id="certificate-reference">{doc.reference}</td>' in content
    assert '<td id="certificate-exporter-name">Test Exporter 1</td>' in content
    assert '<td id="certificate-country">Afghanistan</td>' in content
    assert f'<td id="certificate-goods">{app.product_name}</td>' in content
    assert f'<td id="certificate-issue-date">{issue_date}</td>' in content
    assert '<td id="certificate-status">Valid</td>' in content
    assert '<td id="certificate-document">Error</td>' in content


@patch("web.domains.checker.views.create_presigned_url")
def test_check_cfs_revoked_certifcate(mock_presign_url, exp_client, completed_cfs_app):
    app = completed_cfs_app
    mock_presign_url.return_value = "some-link"
    document_pack.pack_active_revoke(app, "TEST", True)
    cert = document_pack.pack_revoked_get(app)
    doc = cert.document_references.first()
    _add_dummy_document(doc)

    post_data = {
        "certificate_reference": doc.reference,
        "certificate_code": doc.check_code,
        "country": doc.reference_data.country_id,
        "organisation_name": app.exporter.name,
    }
    response = exp_client.post(reverse("checker:certificate-checker"), post_data)
    content = str(response.content)
    issue_date = cert.case_completion_datetime.strftime("%d %B %Y")

    assert response.status_code == HTTPStatus.OK
    assert f"Certificate {doc.reference} has been revoked." in content
    assert f'<td id="certificate-reference">{doc.reference}</td>' in content
    assert f'<td id="certificate-exporter-name">{app.exporter.name}</td>' in content
    assert '<td id="certificate-country">Afghanistan</td>' in content
    assert '<td id="certificate-goods">A Product</td>' in content
    assert f'<td id="certificate-issue-date">{issue_date}</td>' in content
    assert '<td id="certificate-status">Revoked</td>' in content
    assert '<td id="certificate-document"></td>' in content


def test_v1_to_v2_redirect(exp_client):
    response = exp_client.get("/icms/fox/icms/IMP_CERT_CERTIFICATE_CHECKER/check/")
    assert response.status_code == HTTPStatus.MOVED_PERMANENTLY
    assert response.url == reverse("checker:certificate-checker")
