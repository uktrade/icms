from unittest.mock import patch

from django.http import HttpResponse
from pytest_django.asserts import assertRedirects

from web.domains.case.services import document_pack
from web.flow.errors import ProcessStateError, TaskError
from web.tests.conftest import LOGIN_URL
from web.tests.helpers import CaseURLS


def test_fa_oil_preview_licence_view(fa_oil_app_submitted, ilb_admin_client):
    _test_licence_preview(fa_oil_app_submitted, ilb_admin_client)


def test_fa_dfl_preview_licence_view(fa_dfl_app_submitted, ilb_admin_client):
    _test_licence_preview(fa_dfl_app_submitted, ilb_admin_client)


def test_fa_sil_preview_licence_view(fa_sil_app_submitted, ilb_admin_client):
    _test_licence_preview(fa_sil_app_submitted, ilb_admin_client)


def test_fa_oil_pre_sign_licence_view(fa_oil_app_processing, ilb_admin_client):
    _test_licence_pre_sign(fa_oil_app_processing, ilb_admin_client)


def test_fa_dfl_pre_sign_licence_view(fa_dfl_app_pre_sign, ilb_admin_client):
    _test_licence_pre_sign(fa_dfl_app_pre_sign, ilb_admin_client)


def test_fa_sil_pre_sign_licence_view(fa_sil_app_processing, ilb_admin_client):
    _test_licence_pre_sign(fa_sil_app_processing, ilb_admin_client)


def _test_licence_preview(app, ilb_admin_client):
    url = CaseURLS.licence_preview(app.pk)
    response = ilb_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=Licence-Preview.pdf"

    pdf = response.content

    assert pdf.startswith(b"%PDF-")


def _test_licence_pre_sign(app, ilb_admin_client):
    url = CaseURLS.licence_pre_sign(app.pk)
    response = ilb_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=Licence-Preview.pdf"

    pdf = response.content

    assert pdf.startswith(b"%PDF-")


def test_preview_cover_letter_view(fa_oil_app_submitted, ilb_admin_client):
    url = CaseURLS.preview_cover_letter(fa_oil_app_submitted.pk)

    response = ilb_admin_client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == "filename=CoverLetter-Preview.pdf"

    pdf = response.content

    assert pdf.startswith(b"%PDF-")


def test_login_required(fa_oil_app_submitted, cw_client):
    licence_url = CaseURLS.licence_preview(fa_oil_app_submitted.pk)
    cover_letter_url = CaseURLS.preview_cover_letter(fa_oil_app_submitted.pk)

    for url in [licence_url, cover_letter_url]:
        response = cw_client.get(url)
        redirect_url = f"{LOGIN_URL}?next={url}"
        assertRedirects(response, redirect_url, 302), f"URl failed to redirect: {url}"


def test_ilb_admin_permission_required(
    fa_oil_app_submitted, ilb_admin_client, importer_client, exporter_client
):
    licence_url = CaseURLS.licence_preview(fa_oil_app_submitted.pk)
    cover_letter_url = CaseURLS.preview_cover_letter(fa_oil_app_submitted.pk)

    for url in [licence_url, cover_letter_url]:
        response = ilb_admin_client.get(url)
        assert response.status_code == 200

        response = importer_client.get(url)
        assert response.status_code == 403

        response = exporter_client.get(url)
        assert response.status_code == 403


def _add_pre_sign_document_reference(application):
    licence = document_pack.pack_draft_get(application)
    document_pack.doc_ref_licence_create(licence, "0000001B")


@patch("web.domains.case.views.views_pdf.return_pdf", return_value=HttpResponse())
def test_preview_certificate_authorised(mocked_return_pdf, fa_sil_app_processing, ilb_admin_client):
    url = CaseURLS.licence_pre_sign(fa_sil_app_processing.pk)
    response = ilb_admin_client.get(url)
    assert response.status_code == 200


def test_preview_certificate_application_not_authorised(fa_sil_app_submitted, ilb_admin_client):
    url = CaseURLS.licence_pre_sign(fa_sil_app_submitted.pk)
    try:
        ilb_admin_client.get(url)
    except ProcessStateError:
        pass


@patch("web.domains.case.views.views_pdf.return_pdf", return_value=HttpResponse())
def test_preview_certificate_unauthorised_wrong_tasks(
    mocked_return_pdf, fa_sil_app_processing, ilb_admin_client
):
    fa_sil_app_processing.tasks.all().delete()
    url = CaseURLS.licence_pre_sign(fa_sil_app_processing.pk)
    try:
        ilb_admin_client.get(url)
    except TaskError:
        pass
