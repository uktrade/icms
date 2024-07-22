from unittest import mock

from web.domains.case.services import document_pack
from web.models import Constabulary
from web.tests.helpers import CaseURLS


def test_constabulary_documents_view(constabulary_client, completed_dfl_app):
    active_pack = document_pack.pack_active_get(completed_dfl_app)
    response = constabulary_client.get(
        CaseURLS.constabulary_documents(completed_dfl_app.pk, active_pack.pk)
    )
    assert response.status_code == 200


@mock.patch("web.domains.case.views.views_constabulary.get_file_from_s3")
def test_constabulary_documents_download_view(
    mock_get_file_from_s3, constabulary_client, completed_dfl_app
):
    mock_get_file_from_s3.return_value = ""
    active_pack = document_pack.pack_active_get(completed_dfl_app)
    cdr = active_pack.document_references.first()
    response = constabulary_client.get(
        CaseURLS.constabulary_documents_download(completed_dfl_app.pk, active_pack.pk, cdr.pk)
    )
    assert response.status_code == 200
    assert mock_get_file_from_s3.called is True


@mock.patch("web.domains.case.views.views_constabulary.get_file_from_s3")
def test_constabulary_documents_download_view_cdr_not_found(
    mock_get_file_from_s3, constabulary_client, completed_dfl_app
):
    active_pack = document_pack.pack_active_get(completed_dfl_app)
    mock_get_file_from_s3.return_value = ""
    response = constabulary_client.get(
        CaseURLS.constabulary_documents_download(completed_dfl_app.pk, active_pack.pk, 0)
    )
    assert response.status_code == 403
    assert mock_get_file_from_s3.called is False


def test_constabulary_documents_view_as_ilb_admin(ilb_admin_client, completed_dfl_app):
    active_pack = document_pack.pack_active_get(completed_dfl_app)
    response = ilb_admin_client.get(
        CaseURLS.constabulary_documents(completed_dfl_app.pk, active_pack.pk)
    )
    assert response.status_code == 403


def test_constabulary_documents_view_diff_constabulary(constabulary_client, completed_dfl_app):
    cheshire = Constabulary.objects.get(name="Cheshire")
    completed_dfl_app.constabulary = cheshire
    completed_dfl_app.save()
    active_pack = document_pack.pack_active_get(completed_dfl_app)
    response = constabulary_client.get(
        CaseURLS.constabulary_documents(completed_dfl_app.pk, active_pack.pk)
    )
    assert response.status_code == 403


def test_constabulary_documents_view_cfs(constabulary_client, completed_cfs_app):
    active_pack = document_pack.pack_active_get(completed_cfs_app)
    response = constabulary_client.get(
        CaseURLS.constabulary_documents(completed_cfs_app.pk, active_pack.pk)
    )
    assert response.status_code == 404


def test_constabulary_documents_view_sil(constabulary_client, completed_sil_app):
    active_pack = document_pack.pack_active_get(completed_sil_app)
    response = constabulary_client.get(
        CaseURLS.constabulary_documents(completed_sil_app.pk, active_pack.pk)
    )
    assert response.status_code == 403
