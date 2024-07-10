import uuid
from http import HTTPStatus
from unittest import mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import QueryDict
from pytest_django.asserts import assertContains

from web.domains.case.services import document_pack
from web.models import (
    CaseEmail,
    CaseEmailDownloadLink,
    Constabulary,
    ConstabularyLicenceDownloadLink,
)
from web.tests.helpers import CaseURLS


def test_constabulary_documents_view(constabulary_client, completed_dfl_app):
    active_pack = document_pack.pack_active_get(completed_dfl_app)
    response = constabulary_client.get(
        CaseURLS.constabulary_documents(completed_dfl_app.pk, active_pack.pk)
    )
    assert response.status_code == 200


@mock.patch("web.domains.case.views.views_documents.get_file_from_s3")
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


@mock.patch("web.domains.case.views.views_documents.get_file_from_s3")
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


@pytest.fixture()
def dfl_documents_link(completed_dfl_app) -> ConstabularyLicenceDownloadLink:
    return ConstabularyLicenceDownloadLink.objects.create(
        check_code=12345678,
        email="test_user@example.com",  # /PS-IGNORE
        constabulary=Constabulary.objects.get(name="Derbyshire"),
        licence=document_pack.pack_active_get(completed_dfl_app),
    )


class TestDownloadDFLCaseDocumentsFormView:
    @pytest.fixture(autouse=True)
    def setup(self, cw_client, dfl_documents_link):
        self.client = cw_client
        self.link = dfl_documents_link
        self.valid_url = CaseURLS.download_dfl_case_documents(self.link.code)
        qd = QueryDict(mutable=True)
        qd.update(
            {
                "email": self.link.email,
                "constabulary": self.link.constabulary.pk,
                "check_code": self.link.check_code,
            }
        )
        self.valid_query_string = qd.urlencode()
        self.invalid_url = CaseURLS.download_dfl_case_documents(str(uuid.uuid4()))

    def test_get_valid_link(self):
        response = self.client.get(self.valid_url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["form"].initial == {"email": None, "constabulary": None, "check_code": None}

        # Test query parameters load the form initial
        response = self.client.get(self.valid_url + f"?{self.valid_query_string}")
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["form"].initial == {
            "email": self.link.email,
            "constabulary": str(self.link.constabulary.pk),
            "check_code": str(self.link.check_code),
        }

    def test_get_invalid_link(self):
        # Invalid links should still render as if everything is ok
        response = self.client.get(self.invalid_url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["form"].initial == {"email": None, "constabulary": None, "check_code": None}

    @mock.patch("web.domains.case.views.views_documents.create_presigned_url")
    def test_post_valid_link(self, mocked_create_presigned_url):
        # to test the failure_count gets reset
        self.link.failure_count = 2
        self.link.save()

        data = {
            "email": self.link.email,
            "constabulary": self.link.constabulary.pk,
            "check_code": self.link.check_code,
        }

        response = self.client.post(self.valid_url, data=data)
        assert response.status_code == HTTPStatus.OK

        self.link.refresh_from_db()
        assert self.link.failure_count == 0

        context = response.context

        assert context["doc_pack"] == self.link.licence
        assert context["process"] == self.link.licence.import_application.get_specific_model()
        assert (
            context["application_type"] == "Firearms and Ammunition (Deactivated Firearms Licence)"
        )
        licence = context["licence"]
        assert licence["case_reference"] == self.link.licence.case_reference
        assert len(licence["documents"]) == 2
        assert [lic["name"] for lic in licence["documents"]] == ["Cover Letter", "Licence"]

    def test_post_valid_link_expires_after_reaching_failure_limit(self):
        assert self.link.failure_count == 0

        for i in range(1, ConstabularyLicenceDownloadLink.FAILURE_LIMIT + 1):
            data = {
                "email": self.link.email,
                "constabulary": self.link.constabulary.pk,
                "check_code": 87654321,
            }

            response = self.client.post(self.valid_url, data=data)

            assertContains(
                response,
                "If you are having issues downloading the documents click the Regenerate Link button below to resend the email.",
                status_code=HTTPStatus.OK,
            )
            assertContains(response, "Regenerate Link")
            self.link.refresh_from_db()

            assert self.link.failure_count == i

            if i == ConstabularyLicenceDownloadLink.FAILURE_LIMIT:
                assert self.link.expired
            else:
                assert not self.link.expired

    def test_post_invalid_link(self):
        # Invalid links should still render as if everything is ok
        data = {
            "email": self.link.email,
            "constabulary": self.link.constabulary.pk,
            "check_code": 87654321,
        }

        response = self.client.post(self.invalid_url, data=data)

        assertContains(
            response,
            "If you are having issues downloading the documents click the Regenerate Link button below to resend the email.",
            status_code=HTTPStatus.OK,
        )
        assertContains(response, "Regenerate Link")


class TestRegenerateDFLCaseDocumentsDownloadLinkView:
    @pytest.fixture(autouse=True)
    def setup(self, cw_client, dfl_documents_link):
        self.client = cw_client
        self.link = dfl_documents_link
        self.app = dfl_documents_link.licence.import_application.get_specific_model()

        self.valid_url = CaseURLS.regenerate_dfl_case_documents_link(self.link.code)
        self.invalid_url = CaseURLS.regenerate_dfl_case_documents_link(str(uuid.uuid4()))

    def test_post_only(self):
        response = self.client.get(self.valid_url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    @mock.patch(
        "web.domains.case.views.views_documents.send_constabulary_deactivated_firearms_email"
    )
    @mock.patch("web.domains.case.views.views_documents.capture_exception")
    def test_post_valid_link(
        self, mocked_capture_exception, mocked_send_constabulary_deactivated_firearms_email
    ):
        assert not self.link.expired
        response = self.client.post(self.valid_url, follow=True)
        assert response.status_code == HTTPStatus.OK

        messages = list(response.context["messages"])
        assert str(messages[0]) == "If the case exists a new email has been generated."

        # Check the link is now expired (as a new one has been generated)
        self.link.refresh_from_db()
        assert self.link.expired

        # Check the correct related code has been called.
        mocked_send_constabulary_deactivated_firearms_email.assert_called_once_with(self.app)
        mocked_capture_exception.assert_not_called()

    @mock.patch(
        "web.domains.case.views.views_documents.send_constabulary_deactivated_firearms_email"
    )
    @mock.patch("web.domains.case.views.views_documents.capture_exception")
    def test_post_valid_link_unknown_failure(
        self, mocked_capture_exception, mocked_send_constabulary_deactivated_firearms_email
    ):
        mocked_send_constabulary_deactivated_firearms_email.side_effect = RuntimeError(
            "Something unexpected has happened..."
        )

        response = self.client.post(self.valid_url, follow=True)
        assert response.status_code == HTTPStatus.OK

        messages = list(response.context["messages"])
        assert str(messages[0]) == "If the case exists a new email has been generated."

        # Check the correct related code has been called.
        mocked_send_constabulary_deactivated_firearms_email.assert_called_once_with(self.app)
        mocked_capture_exception.assert_called_once()

    @mock.patch(
        "web.domains.case.views.views_documents.send_constabulary_deactivated_firearms_email"
    )
    @mock.patch("web.domains.case.views.views_documents.capture_exception")
    def test_post_invalid_link(
        self, mocked_capture_exception, mocked_send_constabulary_deactivated_firearms_email
    ):
        response = self.client.post(self.invalid_url, follow=True)
        assert response.status_code == HTTPStatus.OK

        messages = list(response.context["messages"])
        assert str(messages[0]) == "If the case exists a new email has been generated."

        # Check no new link was created (as the supplied code was invalid)
        mocked_send_constabulary_deactivated_firearms_email.assert_not_called()
        # And no sentry was raised as an ObjectDoesNotExist was raised
        mocked_capture_exception.assert_not_called()


def generate_case_email_download_link(client, submitted_app, case_type):
    app = submitted_app
    client.post(CaseURLS.take_ownership(app.pk, case_type))
    app.refresh_from_db()
    response = client.post(CaseURLS.create_case_emails(app.pk, case_type))
    app.refresh_from_db()
    case_email: CaseEmail = app.case_emails.last()
    client.post(
        response.url,
        data={
            "to": case_email.to,
            "cc_address_list": [],
            "attachments": case_email.attachments.values_list("pk", flat=True),
            "subject": case_email.subject,
            "body": case_email.body,
            "send": "Send",
        },
    )
    app.refresh_from_db()
    return CaseEmailDownloadLink.objects.get(case_email=case_email)


@pytest.fixture
def beis_case_email_link(ilb_admin_client, gmp_app_submitted):
    return generate_case_email_download_link(ilb_admin_client, gmp_app_submitted, "export")


class TestDownloadBEISEmailDocumentsFormView:
    @pytest.fixture(autouse=True)
    def setup(self, cw_client, beis_case_email_link):
        self.client = cw_client
        self.link = beis_case_email_link
        self.valid_url = CaseURLS.download_case_email_documents(self.link.code)
        qd = QueryDict(mutable=True)
        qd.update(
            {
                "email": self.link.email,
                "check_code": self.link.check_code,
            }
        )
        self.valid_query_string = qd.urlencode()
        self.invalid_url = CaseURLS.download_case_email_documents(str(uuid.uuid4()))

    def test_get_valid_link(self):
        response = self.client.get(self.valid_url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["form"].initial == {"email": None, "check_code": None}

        # Test query parameters load the form initial
        response = self.client.get(self.valid_url + f"?{self.valid_query_string}")
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["form"].initial == {
            "email": self.link.email,
            "check_code": str(self.link.check_code),
        }

    def test_get_invalid_link(self):
        # Invalid links should still render as if everything is ok
        response = self.client.get(self.invalid_url)
        assert response.status_code == HTTPStatus.OK

        context = response.context
        assert context["form"].initial == {"email": None, "check_code": None}

    @mock.patch("web.domains.case.views.views_documents.create_presigned_url")
    def test_post_valid_link(self, mocked_create_presigned_url):
        # to test the failure_count gets reset
        self.link.failure_count = 2
        self.link.save()

        data = {
            "email": self.link.email,
            "check_code": self.link.check_code,
        }

        response = self.client.post(self.valid_url, data=data)
        assert response.status_code == HTTPStatus.OK

        self.link.refresh_from_db()
        assert self.link.failure_count == 0

        context = response.context

        assert context["exporter"]["name"] == "Test Exporter 1"
        assert len(context["documents"]) == 3
        assert [doc["name"] for doc in context["documents"]] == [
            "ISO 17065",
            "ISO 17021",
            "ISO 22716",
        ]

    def test_post_valid_link_expires_after_reaching_failure_limit(self):
        assert self.link.failure_count == 0

        for i in range(1, CaseEmailDownloadLink.FAILURE_LIMIT + 1):
            data = {"email": self.link.email, "check_code": 1}

            response = self.client.post(self.valid_url, data=data)

            assertContains(
                response,
                "If you are having issues downloading the documents click the Regenerate Link button below to resend the email.",
                status_code=HTTPStatus.OK,
            )
            assertContains(response, "Regenerate Link")
            self.link.refresh_from_db()

            assert self.link.failure_count == i

            if i == CaseEmailDownloadLink.FAILURE_LIMIT:
                assert self.link.expired
            else:
                assert not self.link.expired

    def test_post_invalid_link(self):
        # Invalid links should still render as if everything is ok
        data = {"email": self.link.email, "check_code": 1}

        response = self.client.post(self.invalid_url, data=data)

        assertContains(
            response,
            "If you are having issues downloading the documents click the Regenerate Link button below to resend the email.",
            status_code=HTTPStatus.OK,
        )
        assertContains(response, "Regenerate Link")


class TestRegenerateBEISCaseEmailDownloadLinkView:
    @pytest.fixture(autouse=True)
    def setup(self, cw_client, beis_case_email_link):
        self.client = cw_client
        self.link = beis_case_email_link

        self.valid_url = CaseURLS.regenerate_case_email_documents_link(self.link.code)
        self.invalid_url = CaseURLS.regenerate_case_email_documents_link(str(uuid.uuid4()))

    def test_post_only(self):
        response = self.client.get(self.valid_url)
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED

    @mock.patch("web.domains.case.views.views_documents.send_case_email")
    @mock.patch("web.domains.case.views.views_documents.capture_exception")
    def test_post_valid_link_arse(self, mocked_capture_exception, mocked_send_case_email):
        assert not self.link.expired
        response = self.client.post(self.valid_url, follow=True)
        assert response.status_code == HTTPStatus.OK

        messages = list(response.context["messages"])
        assert str(messages[0]) == "If the case exists a new email has been generated."

        # Check the link is now expired (as a new one has been generated)
        self.link.refresh_from_db()
        assert self.link.expired

        # Check the correct related code has been called.
        mocked_send_case_email.assert_called_once_with(self.link.case_email, AnonymousUser())
        mocked_capture_exception.assert_not_called()

    @mock.patch("web.domains.case.views.views_documents.send_case_email")
    @mock.patch("web.domains.case.views.views_documents.capture_exception")
    def test_post_valid_link_unknown_failure(
        self, mocked_capture_exception, mocked_send_case_email
    ):
        mocked_send_case_email.side_effect = RuntimeError("Something unexpected has happened...")

        response = self.client.post(self.valid_url, follow=True)
        assert response.status_code == HTTPStatus.OK

        messages = list(response.context["messages"])
        assert str(messages[0]) == "If the case exists a new email has been generated."

        # Check the correct related code has been called.
        mocked_send_case_email.assert_called_once_with(self.link.case_email, AnonymousUser())
        mocked_capture_exception.assert_called_once()

    @mock.patch("web.domains.case.views.views_documents.send_case_email")
    @mock.patch("web.domains.case.views.views_documents.capture_exception")
    def test_post_invalid_link(self, mocked_capture_exception, mocked_send_case_email):
        response = self.client.post(self.invalid_url, follow=True)
        assert response.status_code == HTTPStatus.OK

        messages = list(response.context["messages"])
        assert str(messages[0]) == "If the case exists a new email has been generated."

        # Check no new link was created (as the supplied code was invalid)
        mocked_send_case_email.assert_not_called()
        # And no sentry was raised as an ObjectDoesNotExist was raised
        mocked_capture_exception.assert_not_called()
