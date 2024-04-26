from unittest import mock

from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertRedirects, assertTemplateUsed

from web.domains.case.forms import CaseEmailResponseForm
from web.models import CaseEmail as CaseEmailModel
from web.tests.auth import AuthTestCase
from web.tests.helpers import CaseURLS


class TestViewEmail(AuthTestCase):
    def create_case_for_application(self, app) -> WSGIRequest:
        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk))
        resp = self.ilb_admin_client.post(CaseURLS.create_case_emails(app.pk))
        assert app.case_emails.count() == 1
        return resp

    def test_manage_constabulary_emails_get(self, fa_dfl_app_submitted):
        resp = self.ilb_admin_client.get(CaseURLS.manage_case_emails(fa_dfl_app_submitted.pk))
        assert resp.status_code == 200

        assertContains(resp, "Manage Emails")
        assertTemplateUsed(resp, "web/domains/case/manage/case-emails.html")

        assert resp.context["case_emails"].count() == 0

        # Firearms applications display constabulary emails
        assert resp.context["info_email"] == (
            "This screen is used to email relevant constabularies. You may attach multiple"
            " firearms certificates to a single email. You can also record responses from the constabulary."
        )
        assert resp.context["email_title"] == "Emails"
        assert resp.context["email_subtitle"] == ""
        assert resp.context["no_emails_msg"] == "There aren't any emails."

    def test_manage_cfs_hse_emails_get(self, cfs_app_submitted):
        app = cfs_app_submitted

        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))
        response = self.ilb_admin_client.get(CaseURLS.manage_case_emails(app.pk, "export"))

        assert response.status_code == 200
        assert response.context["case_emails"].count() == 0

        assertTemplateUsed(response, "web/domains/case/manage/case-emails.html")
        assert response.context["info_email"] == (
            "Biocidal products: this screen is used to email and record responses from"
            " the Health and Safety Executive."
        )
        assert response.context["email_title"] == "Health and Safety Executive (HSE) Checks"
        assert response.context["email_subtitle"] == "HSE Emails"
        assert response.context["no_emails_msg"] == "There aren't any HSE emails."

    def test_create_case_email(self, fa_dfl_app_submitted):
        resp = self.create_case_for_application(fa_dfl_app_submitted)
        case_email = fa_dfl_app_submitted.case_emails.get()
        assertRedirects(
            resp, CaseURLS.edit_case_emails(fa_dfl_app_submitted.pk, case_email.pk), 302
        )

    @mock.patch("web.domains.case.views.views_email.send_case_email")
    def test_edit_case_email(self, mock_send_case_email, fa_dfl_app_submitted):
        self.create_case_for_application(fa_dfl_app_submitted)
        case_email = fa_dfl_app_submitted.case_emails.get()

        resp = self.ilb_admin_client.post(
            CaseURLS.edit_case_emails(fa_dfl_app_submitted.pk, case_email.pk),
            data={
                "subject": "TEST EMAIL",
                "body": "TEST EMAIL BODY",
                "to": self.importer_user.email,
            },
            follow=True,
        )
        assert resp.status_code == 200
        assert resp.context["form"].errors == {}
        case_email.refresh_from_db()
        assert case_email.subject == "TEST EMAIL"
        assert case_email.body == "TEST EMAIL BODY"
        assert case_email.to == self.importer_user.email
        assert mock_send_case_email.called is False

    @mock.patch("web.domains.case.views.views_email.send_case_email")
    def test_edit_case_email_and_send(self, mock_send_case_email, fa_dfl_app_submitted):
        mock_send_case_email.return_value = None
        self.create_case_for_application(fa_dfl_app_submitted)
        case_email = fa_dfl_app_submitted.case_emails.get()

        resp = self.ilb_admin_client.post(
            CaseURLS.edit_case_emails(fa_dfl_app_submitted.pk, case_email.pk),
            data={
                "subject": "TEST EMAIL",
                "body": "TEST EMAIL BODY",
                "to": self.importer_user.email,
                "send": True,
            },
            follow=True,
        )
        assert resp.status_code == 200
        case_email.refresh_from_db()
        assert case_email.subject == "TEST EMAIL"
        assert case_email.body == "TEST EMAIL BODY"
        assert case_email.to == self.importer_user.email
        assert mock_send_case_email.called is True

    def test_archive_case_email(self, fa_dfl_app_submitted):
        self.create_case_for_application(fa_dfl_app_submitted)
        case_email = fa_dfl_app_submitted.case_emails.get()
        assert case_email.is_active is True
        resp = self.ilb_admin_client.post(
            CaseURLS.archive_case_emails(fa_dfl_app_submitted.pk, case_email.pk),
        )
        assert resp.status_code == 302
        case_email.refresh_from_db()
        assert case_email.is_active is False

    def test_add_response_to_case_email(self, fa_dfl_app_submitted):
        self.create_case_for_application(fa_dfl_app_submitted)
        case_email = fa_dfl_app_submitted.case_emails.get()
        case_email.status = CaseEmailModel.Status.OPEN
        case_email.sent_datetime = timezone.now()
        case_email.save()

        resp = self.ilb_admin_client.get(
            CaseURLS.add_response_case_emails(fa_dfl_app_submitted.pk, case_email.pk),
        )
        assert resp.status_code == 200

        resp = self.ilb_admin_client.post(
            CaseURLS.add_response_case_emails(fa_dfl_app_submitted.pk, case_email.pk),
            data={"response": "Email actioned"},
        )
        assert resp.status_code == 302
        case_email.refresh_from_db()
        assert case_email.status == CaseEmailModel.Status.CLOSED
        assert case_email.response == "Email actioned"

    def test_all_response_forms_shown(self, cfs_app_submitted):
        app = cfs_app_submitted
        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, case_type="export"))

        self.ilb_admin_client.post(CaseURLS.create_case_emails(app.pk, case_type="export"))
        self.ilb_admin_client.post(CaseURLS.create_case_emails(app.pk, case_type="export"))
        response = self.ilb_admin_client.get(CaseURLS.manage_case_emails(app.pk, "export"))

        assert response.status_code == 200
        assertTemplateUsed(response, "web/domains/case/manage/case-emails.html")

        case_emails = response.context["case_emails"]
        assert case_emails.count() == 2

        # assert that two forms are in the response body
        url = reverse(
            "case:add-response-case-email",
            kwargs={
                "application_pk": app.pk,
                "case_email_pk": case_emails[0].pk,
                "case_type": "export",
            },
        )
        form_finder = f'action="{url}"'
        assert form_finder in response.content.decode()

        url = reverse(
            "case:add-response-case-email",
            kwargs={
                "application_pk": app.pk,
                "case_email_pk": case_emails[1].pk,
                "case_type": "export",
            },
        )
        form_finder = f'action="{url}"'
        assert form_finder in response.content.decode()

        assert isinstance(response.context["record_response_form"], CaseEmailResponseForm)

    def test_responded_emails_not_shown(self, cfs_app_submitted):
        app = cfs_app_submitted
        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, case_type="export"))

        self.ilb_admin_client.post(CaseURLS.create_case_emails(app.pk, case_type="export"))
        self.ilb_admin_client.post(CaseURLS.create_case_emails(app.pk, case_type="export"))

        # now we mark one of them as responded to and confirm the form to respond no longer appears
        completed_case_email = CaseEmailModel.objects.last()
        completed_case_email.response = "test"
        completed_case_email.save()

        response = self.ilb_admin_client.get(CaseURLS.manage_case_emails(app.pk, "export"))
        case_emails = response.context["case_emails"]
        assert case_emails.count() == 2

        url = reverse(
            "case:add-response-case-email",
            kwargs={
                "application_pk": app.pk,
                "case_email_pk": completed_case_email.pk,
                "case_type": "export",
            },
        )
        form_finder = f'action="{url}"'
        assert form_finder not in response.content.decode()

        url = reverse(
            "case:add-response-case-email",
            kwargs={
                "application_pk": app.pk,
                "case_email_pk": CaseEmailModel.objects.exclude(pk=completed_case_email.pk)
                .get()
                .pk,
                "case_type": "export",
            },
        )
        form_finder = f'action="{url}"'
        assert form_finder in response.content.decode()
