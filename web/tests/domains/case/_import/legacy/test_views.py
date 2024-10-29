from http import HTTPStatus
from unittest import mock

from django.urls import reverse
from pytest_django.asserts import assertRedirects

from web.models import OutwardProcessingTradeFile, PriorSurveillanceContractFile
from web.tests.application_fixtures import add_dummy_file
from web.tests.helpers import CaseURLS, get_messages_from_response


class TestOPTView:

    @mock.patch("web.domains.case.utils.get_file_from_s3")
    def test_view_document(self, mock_get_file_from_s3, opt_app_submitted, ilb_admin_client):
        mock_get_file_from_s3.return_value = b"test_file"
        app = opt_app_submitted
        app.documents.add(
            add_dummy_file(
                OutwardProcessingTradeFile,
                file_type=OutwardProcessingTradeFile.Type.FQ_EMPLOYMENT_DECREASED,
            )
        )
        document_pk = app.documents.first().pk
        manage_checklist = CaseURLS.opt_view_document(app.pk, document_pk)
        resp = ilb_admin_client.get(manage_checklist, follow=True)
        assert resp.status_code == HTTPStatus.OK
        assert resp.headers["Content-Disposition"] == 'attachment; filename="dummy-filename"'

    def test_manage_checklist(self, opt_app_submitted, ilb_admin_client):
        app = opt_app_submitted
        url = CaseURLS.opt_checklist(app.pk)
        resp = ilb_admin_client.post(url, follow=True)
        assert resp.status_code == HTTPStatus.OK
        assert resp.context["form"].errors == {}
        assert resp.context["page_title"] == "Outward Processing Trade Licence - Checklist"


class TestTextilesView:

    @mock.patch("web.domains.case.utils.get_file_from_s3")
    def test_view_document(self, mock_get_file_from_s3, textiles_app_submitted, ilb_admin_client):
        mock_get_file_from_s3.return_value = b"test_file"
        app = textiles_app_submitted
        document_pk = app.supporting_documents.first().pk
        manage_checklist = CaseURLS.textiles_view_document(app.pk, document_pk)
        resp = ilb_admin_client.get(manage_checklist, follow=True)
        assert resp.status_code == HTTPStatus.OK
        assert resp.headers["Content-Disposition"] == 'attachment; filename="dummy-filename"'

    def test_manage_checklist(self, textiles_app_submitted, ilb_admin_client):
        app = textiles_app_submitted
        manage_checklist = CaseURLS.textiles_checklist(app.pk)
        resp = ilb_admin_client.post(manage_checklist, follow=True)
        assert resp.status_code == HTTPStatus.OK
        assert resp.context["form"].errors == {}
        assert resp.context["page_title"] == "Textiles (Quota) Import Licence - Checklist"


class TestSPSView:

    @mock.patch("web.domains.case.utils.get_file_from_s3")
    def test_sps_view_document(self, mock_get_file_from_s3, sps_app_submitted, ilb_admin_client):
        mock_get_file_from_s3.return_value = b"test_file"
        app = sps_app_submitted
        document_pk = app.supporting_documents.first().pk
        url = CaseURLS.sps_view_document(app.pk, document_pk)
        resp = ilb_admin_client.get(url)

        assert resp.status_code == HTTPStatus.OK
        assert resp.headers["Content-Disposition"] == 'attachment; filename="dummy-filename"'
        assert mock_get_file_from_s3.called is True

    @mock.patch("web.domains.case.utils.get_file_from_s3")
    def test_sps_view_contract_document_without_contract(
        self, mock_get_file_from_s3, sps_app_submitted, ilb_admin_client
    ):
        mock_get_file_from_s3.return_value = b"test_file"
        app = sps_app_submitted
        url = CaseURLS.sps_view_contract_document(app.pk)
        resp = ilb_admin_client.get(url)

        expected_redirect = reverse(
            "case:view", kwargs={"application_pk": app.pk, "case_type": "import"}
        )
        assertRedirects(resp, expected_redirect, HTTPStatus.FOUND)
        messages = get_messages_from_response(resp)
        assert len(messages) == 1
        assert messages[0] == "The application does not have contract/invoice attached."
        assert mock_get_file_from_s3.called is False

    @mock.patch("web.domains.case.utils.get_file_from_s3")
    def test_sps_view_contract_document(
        self, mock_get_file_from_s3, sps_app_submitted, ilb_admin_client
    ):
        mock_get_file_from_s3.return_value = b"test_file"
        app = sps_app_submitted

        contract_file = PriorSurveillanceContractFile.objects.create(
            path="dummy-path",
            filename="dummy-filename",
            content_type="application/pdf",
            file_size=100,
            created_by_id=0,
            file_type=PriorSurveillanceContractFile.Type.SUPPLY_CONTRACT,
        )
        app.contract_file = contract_file
        app.save()

        url = CaseURLS.sps_view_contract_document(app.pk)
        resp = ilb_admin_client.get(url)
        assert resp.status_code == HTTPStatus.OK
        assert resp.headers["Content-Disposition"] == 'attachment; filename="dummy-filename"'
        assert mock_get_file_from_s3.called is True
