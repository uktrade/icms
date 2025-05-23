from unittest import mock

from django.core.handlers.wsgi import WSGIRequest
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains, assertRedirects, assertTemplateUsed

from web.domains.case.forms import CaseEmailResponseForm
from web.models import CaseEmail
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
        assert resp.context["email_title"] == "Constabulary Emails"
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

    def test_manage_nuclear_materials_emails_get(self, nuclear_app_processing):
        resp = self.ilb_admin_client.get(CaseURLS.manage_case_emails(nuclear_app_processing.pk))
        assert resp.status_code == 200

        assertContains(resp, "Manage Emails")
        assertTemplateUsed(resp, "web/domains/case/manage/case-emails.html")

        assert resp.context["case_emails"].count() == 0

        assert resp.context["email_title"] == "Nuclear Material Import Licence Emails"
        assert resp.context["email_subtitle"] == ""
        assert resp.context["no_emails_msg"] == "There aren't any emails."

    def test_create_case_email(self, fa_dfl_app_submitted):
        resp = self.create_case_for_application(fa_dfl_app_submitted)
        case_email = fa_dfl_app_submitted.case_emails.get()
        assertRedirects(
            resp, CaseURLS.edit_case_emails(fa_dfl_app_submitted.pk, case_email.pk), 302
        )

    def test_create_nuclear_material_case_email(self, nuclear_app_submitted):
        app = nuclear_app_submitted
        resp = self.create_case_for_application(app)
        case_email = app.case_emails.get()
        assertRedirects(resp, CaseURLS.edit_case_emails(app.pk, case_email.pk), 302)

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
        case_email.status = CaseEmail.Status.OPEN
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
        assert case_email.status == CaseEmail.Status.CLOSED
        assert case_email.response == "Email actioned"

    def test_all_response_forms_shown(self, cfs_app_submitted):
        app = cfs_app_submitted
        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, case_type="export"))

        self.ilb_admin_client.post(CaseURLS.create_case_emails(app.pk, case_type="export"))
        self.ilb_admin_client.post(CaseURLS.create_case_emails(app.pk, case_type="export"))

        # fake both emails being sent (so we can record response)
        app.refresh_from_db()
        app.case_emails.all().update(status=CaseEmail.Status.OPEN)

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

        # fake both emails being sent (so we can record response)
        app.refresh_from_db()
        app.case_emails.all().update(status=CaseEmail.Status.OPEN)

        # now we mark one of them as responded to and confirm the form to respond no longer appears
        completed_case_email = CaseEmail.objects.last()
        completed_case_email.status = CaseEmail.Status.CLOSED
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
                "case_email_pk": CaseEmail.objects.exclude(pk=completed_case_email.pk).get().pk,
                "case_type": "export",
            },
        )
        form_finder = f'action="{url}"'
        assert form_finder in response.content.decode()

    def test_hse_email_count_sidebar(self, cfs_app_submitted):
        self.ilb_admin_client.post(
            CaseURLS.take_ownership(cfs_app_submitted.pk, case_type="export")
        )

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(cfs_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == 200
        assert "HSE Emails (0/0)" in resp.content.decode()

        # create a case email
        self.ilb_admin_client.post(
            CaseURLS.create_case_emails(cfs_app_submitted.pk, case_type="export")
        )

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(cfs_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == 200
        assert "HSE Emails (0/1)" in resp.content.decode()

        # now we mark one of them as open to and confirm that the count updates accordingly
        completed_case_email = CaseEmail.objects.last()
        completed_case_email.status = CaseEmail.Status.OPEN
        completed_case_email.save()

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(cfs_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == 200
        assert "HSE Emails (1/1)" in resp.content.decode()

        # now we mark one of them as closed to and confirm that the count updates accordingly
        completed_case_email.status = CaseEmail.Status.CLOSED
        completed_case_email.save()

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(cfs_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == 200
        assert "HSE Emails (0/1)" in resp.content.decode()

    def test_beis_email_count_sidebar(self, gmp_app_submitted):
        self.ilb_admin_client.post(
            CaseURLS.take_ownership(gmp_app_submitted.pk, case_type="export")
        )

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(gmp_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == 200
        assert "BEIS Emails (0/0)" in resp.content.decode()

        # create a case email
        self.ilb_admin_client.post(
            CaseURLS.create_case_emails(gmp_app_submitted.pk, case_type="export")
        )

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(gmp_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == 200
        assert "BEIS Emails (0/1)" in resp.content.decode()

        # now we mark one of them as open to and confirm that the count updates accordingly
        completed_case_email = CaseEmail.objects.last()
        completed_case_email.status = CaseEmail.Status.OPEN
        completed_case_email.save()

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(gmp_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == 200
        assert "BEIS Emails (1/1)" in resp.content.decode()

        # now we mark one of them as closed to and confirm that the count updates accordingly
        completed_case_email.status = CaseEmail.Status.CLOSED
        completed_case_email.save()

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(gmp_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == 200
        assert "BEIS Emails (0/1)" in resp.content.decode()

    def test_verified_authorities_empty(self, gmp_app_submitted):
        self.ilb_admin_client.post(
            CaseURLS.take_ownership(gmp_app_submitted.pk, case_type="export")
        )

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(gmp_app_submitted.pk, case_type="export")
        )
        assert resp.context["verified_section_5_authorities"] == []
        assert resp.context["verified_firearms_authorities"] == []

    def test_verified_section5_authorities_none_expired(
        self, fa_sil_app_submitted, section5_authority
    ):
        section5_authority.start_date = timezone.now() - timezone.timedelta(days=1)
        section5_authority.end_date = timezone.now() + timezone.timedelta(days=1)
        section5_authority.save()
        fa_sil_app_submitted.verified_section5.add(section5_authority)
        self.ilb_admin_client.post(
            CaseURLS.take_ownership(fa_sil_app_submitted.pk, case_type="import")
        )

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(fa_sil_app_submitted.pk, case_type="import")
        )
        verified_section5_authorities = resp.context["verified_section_5_authorities"]
        assert verified_section5_authorities.count() == 1
        assert verified_section5_authorities[0] == section5_authority
        assert (
            "One or more verified Section 5 Authorities have been selected by the applicant"
            in resp.content.decode()
        )
        assert "At least one verified Section 5 Authority has expired" not in resp.content.decode()

    def test_verified_section5_authorities_some_expired(
        self, fa_sil_app_submitted, section5_authority
    ):
        section5_authority.start_date = timezone.now() - timezone.timedelta(days=2)
        section5_authority.end_date = timezone.now() - timezone.timedelta(days=1)
        section5_authority.save()
        fa_sil_app_submitted.verified_section5.add(section5_authority)
        self.ilb_admin_client.post(
            CaseURLS.take_ownership(fa_sil_app_submitted.pk, case_type="import")
        )

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(fa_sil_app_submitted.pk, case_type="import")
        )
        verified_section5_authorities = resp.context["verified_section_5_authorities"]
        assert verified_section5_authorities.count() == 1
        assert verified_section5_authorities[0] == section5_authority
        assert (
            "One or more verified Section 5 Authorities have been selected by the applicant"
            in resp.content.decode()
        )
        assert "At least one verified Section 5 Authority has expired" in resp.content.decode()

    def test_verified_firearms_authorities_none_expired(
        self, fa_sil_app_submitted, firearms_authority
    ):
        firearms_authority.start_date = timezone.now() - timezone.timedelta(days=1)
        firearms_authority.end_date = timezone.now() + timezone.timedelta(days=1)
        firearms_authority.save()
        fa_sil_app_submitted.verified_certificates.add(firearms_authority)
        self.ilb_admin_client.post(
            CaseURLS.take_ownership(fa_sil_app_submitted.pk, case_type="import")
        )

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(fa_sil_app_submitted.pk, case_type="import")
        )
        verified_firearms_authorities = resp.context["verified_firearms_authorities"]
        assert verified_firearms_authorities.count() == 1
        assert verified_firearms_authorities[0] == firearms_authority
        assert (
            "One or more verified Firearms Authorities have been selected by the applicant"
            in resp.content.decode()
        )
        assert "At least one verified Firearms Authority has expired" not in resp.content.decode()

    def test_verified_firearms_authorities_some_expired(
        self, fa_sil_app_submitted, firearms_authority
    ):
        firearms_authority.start_date = timezone.now() - timezone.timedelta(days=2)
        firearms_authority.end_date = timezone.now() - timezone.timedelta(days=2)
        firearms_authority.save()
        fa_sil_app_submitted.verified_certificates.add(firearms_authority)
        self.ilb_admin_client.post(
            CaseURLS.take_ownership(fa_sil_app_submitted.pk, case_type="import")
        )

        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(fa_sil_app_submitted.pk, case_type="import")
        )
        verified_firearms_authorities = resp.context["verified_firearms_authorities"]
        assert verified_firearms_authorities.count() == 1
        assert verified_firearms_authorities[0] == firearms_authority
        assert (
            "One or more verified Firearms Authorities have been selected by the applicant"
            in resp.content.decode()
        )
        assert "At least one verified Firearms Authority has expired" in resp.content.decode()

    def test_oil_app_doesnt_have_section5(self, fa_oil_app_submitted, firearms_authority):
        firearms_authority.start_date = timezone.now() - timezone.timedelta(days=2)
        firearms_authority.end_date = timezone.now() + timezone.timedelta(days=2)
        firearms_authority.save()
        fa_oil_app_submitted.verified_certificates.add(firearms_authority)
        self.ilb_admin_client.post(
            CaseURLS.take_ownership(fa_oil_app_submitted.pk, case_type="import")
        )
        resp = self.ilb_admin_client.get(
            CaseURLS.manage_case_emails(fa_oil_app_submitted.pk, case_type="import")
        )
        assert resp.context["verified_section_5_authorities"] == []
        assert resp.context["verified_firearms_authorities"].count() == 1
        assert resp.context["verified_firearms_authorities"][0] == firearms_authority
