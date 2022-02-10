from pytest_django.asserts import assertRedirects

from web.tests.helpers import CaseURLS


def test_preview_licence_view(fa_oil_app_submitted, icms_admin_client):
    url = CaseURLS.licence_preview(fa_oil_app_submitted.pk)

    response = icms_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=Licence-Preview.pdf"

    pdf = response.content

    assert pdf.startswith(b"%PDF-")


def test_licence_pre_sign_view(fa_oil_app_submitted, icms_admin_client):
    url = CaseURLS.licence_pre_sign(fa_oil_app_submitted.pk)

    response = icms_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=Licence-Preview.pdf"

    pdf = response.content

    assert pdf.startswith(b"%PDF-")


def test_preview_cover_letter_view(fa_oil_app_submitted, icms_admin_client):
    url = CaseURLS.preview_cover_letter(fa_oil_app_submitted.pk)

    response = icms_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=CoverLetter.pdf"

    pdf = response.content

    assert pdf.startswith(b"%PDF-")


def test_login_required(fa_oil_app_submitted, client):
    licence_url = CaseURLS.licence_preview(fa_oil_app_submitted.pk)
    cover_letter_url = CaseURLS.preview_cover_letter(fa_oil_app_submitted.pk)

    for url in [licence_url, cover_letter_url]:
        response = client.get(url)
        redirect_url = f"/?next={url}"
        assertRedirects(response, redirect_url, 302), f"URl failed to redirect: {url}"
