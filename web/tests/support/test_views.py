from http import HTTPStatus

import pytest
from django.shortcuts import reverse

from web.sites import SiteName


def test_accessibility_statement(importer_client, exporter_client, ilb_admin_client, imp_client):
    url = reverse("support:accessibility-statement")
    exp_str = "This accessibility statement applies to the service %s"

    response = imp_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str % SiteName.IMPORTER.label in response.content.decode()

    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str % SiteName.IMPORTER.label in response.content.decode()

    response = exporter_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str % SiteName.EXPORTER.label in response.content.decode()

    response = ilb_admin_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str % SiteName.CASEWORKER.label in response.content.decode()


def test_support_landing_page(importer_client, exporter_client, ilb_admin_client, imp_client):
    url = reverse("support:landing")
    exp_str = "Help and support"

    response = imp_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str in response.content.decode()

    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str in response.content.decode()

    response = exporter_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str in response.content.decode()

    response = ilb_admin_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str in response.content.decode()


@pytest.mark.parametrize(
    "view_name,exp_str",
    (
        ("support:validate-signature", "What date was your document issued"),
        (
            "support:validate-signature-v1",
            "Use this guide if your documents were issued before 26th September 2024",
        ),
        (
            "support:validate-signature-v2",
            "Use this guide if your documents were issued after 25th September 2024",
        ),
    ),
)
def test_validate_signature_pages(
    importer_client, exporter_client, ilb_admin_client, imp_client, view_name, exp_str
):
    url = reverse(view_name)

    response = imp_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str in response.content.decode()

    response = importer_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str in response.content.decode()

    response = exporter_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str in response.content.decode()

    response = ilb_admin_client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert exp_str in response.content.decode()


@pytest.mark.parametrize(
    "date_issued,exp_view_name",
    (
        ("08-Aug-2024", "support:validate-signature-v1"),
        ("30-Sep-2024", "support:validate-signature-v2"),
    ),
)
def test_validate_signature_page_form(importer_client, date_issued, exp_view_name):
    url = reverse("support:validate-signature")
    response = importer_client.post(url, data={"date_issued": date_issued})
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse(exp_view_name)


def test_validate_signature_page_form_error(importer_client):
    url = reverse("support:validate-signature")
    response = importer_client.post(url, data={"date_issued": "hello"})
    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors == {"date_issued": ["Enter a valid date."]}
