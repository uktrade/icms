import pytest
from django.conf import settings
from freezegun import freeze_time

from web.mail.constants import EmailTypes
from web.mail.emails import create_case_email, send_case_email
from web.models import CaseEmail as CaseEmailModel
from web.models import EmailTemplate
from web.sites import get_exporter_site_domain, get_importer_site_domain
from web.tests.auth.auth import AuthTestCase
from web.tests.helpers import CaseURLS


class TestExportCaseEmails(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, mock_gov_notify_client):
        self.mock_gov_notify_client = mock_gov_notify_client
        self.exp_template_id = str(
            EmailTemplate.objects.get(name=EmailTypes.CASE_EMAIL).gov_notify_template_id
        )

    def test_create_gmp_case_beis_email(self, gmp_app_submitted):
        app = gmp_app_submitted
        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))
        app.refresh_from_db()

        attachments = app.supporting_documents.filter(is_active=True)
        case_email = create_case_email(
            app,
            EmailTypes.BEIS_CASE_EMAIL,
            "to_address@example.com",  # /PS-IGNORE
            attachments=attachments,
        )

        assert case_email.to == "to_address@example.com"  # /PS-IGNORE

        case_email_file_pks = case_email.attachments.values_list("pk", flat=True).order_by("pk")
        gmp_file_pks = attachments.values_list("pk", flat=True).order_by("pk")

        assert list(case_email_file_pks) == list(gmp_file_pks)
        assert case_email.subject == "Good Manufacturing Practice Application Enquiry"
        assert (
            "We have received a Certificate of Good Manufacturing Practice application"
            in case_email.body
        )

    @freeze_time("2024-01-01 12:00:00")
    def test_send_gmp_case_beis_email(self, gmp_app_submitted):
        self.ilb_admin_client.post(CaseURLS.take_ownership(gmp_app_submitted.pk, "export"))
        gmp_app_submitted.refresh_from_db()
        case_email = create_case_email(
            gmp_app_submitted,
            EmailTypes.BEIS_CASE_EMAIL,
            "to_address@example.com",  # /PS-IGNORE
        )
        assert case_email.status == CaseEmailModel.Status.DRAFT
        send_case_email(case_email)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 1
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "to_address@example.com",  # /PS-IGNORE
            self.exp_template_id,
            personalisation={
                "subject": "Good Manufacturing Practice Application Enquiry",
                "body": case_email.body,
                "icms_url": get_exporter_site_domain(),
                "icms_contact_email": settings.ILB_CONTACT_EMAIL,
                "icms_contact_phone": settings.ILB_CONTACT_PHONE,
            },
        )
        case_email.refresh_from_db()
        assert case_email.status == CaseEmailModel.Status.OPEN
        assert case_email.sent_datetime.isoformat() == "2024-01-01T12:00:00+00:00"

    def test_create_cfs_case_hse_email(self, cfs_app_submitted):
        app = cfs_app_submitted

        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))
        app.refresh_from_db()

        case_email = create_case_email(
            app, EmailTypes.HSE_CASE_EMAIL, "to_address@example.com"  # /PS-IGNORE
        )

        assert case_email.to == "to_address@example.com"  # /PS-IGNORE
        assert case_email.subject == "Biocidal Product Enquiry"
        assert "The application is for the following biocidal products" in case_email.body


class TestImportCaseEmails(AuthTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, _setup, mock_gov_notify_client):
        self.mock_gov_notify_client = mock_gov_notify_client
        self.exp_template_id = str(
            EmailTemplate.objects.get(name=EmailTypes.CASE_EMAIL).gov_notify_template_id
        )

    def test_create_dfl_constabulary_email(self, fa_dfl_app_submitted):
        app = fa_dfl_app_submitted

        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "import"))
        app.refresh_from_db()

        case_email = create_case_email(
            app, EmailTypes.CONSTABULARY_CASE_EMAIL, cc=["cc_address@example.com"]  # /PS-IGNORE
        )

        assert case_email.to is None
        assert case_email.cc_address_list == ["cc_address@example.com"]  # /PS-IGNORE
        assert case_email.subject == "Import Licence RFD Enquiry"
        assert "\ngoods_description value\n" in case_email.body

    def test_send_dfl_constabulary_email(self, fa_dfl_app_submitted):
        self.ilb_admin_client.post(CaseURLS.take_ownership(fa_dfl_app_submitted.pk, "import"))
        fa_dfl_app_submitted.refresh_from_db()
        case_email = create_case_email(
            fa_dfl_app_submitted,
            EmailTypes.CONSTABULARY_CASE_EMAIL,
            "to_address@example.com",  # /PS-IGNORE
            cc=["cc_address@example.com", "to_address@example.com"],  # /PS-IGNORE
        )
        send_case_email(case_email)
        assert self.mock_gov_notify_client.send_email_notification.call_count == 2
        self.mock_gov_notify_client.send_email_notification.assert_any_call(
            "to_address@example.com",  # /PS-IGNORE
            self.exp_template_id,
            personalisation={
                "subject": "Import Licence RFD Enquiry",
                "body": case_email.body,
                "icms_url": get_importer_site_domain(),
                "icms_contact_email": settings.ILB_CONTACT_EMAIL,
                "icms_contact_phone": settings.ILB_CONTACT_PHONE,
            },
        )

    def test_create_oil_constabulary_email(self, fa_oil_app_submitted):
        app = fa_oil_app_submitted

        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "import"))
        app.refresh_from_db()

        case_email = create_case_email(
            app, EmailTypes.CONSTABULARY_CASE_EMAIL, cc=["cc_address@example.com"]  # /PS-IGNORE
        )

        assert case_email.to is None
        assert case_email.cc_address_list == ["cc_address@example.com"]  # /PS-IGNORE
        assert case_email.subject == "Import Licence RFD Enquiry"

        assert (
            "\nFirearms, component parts thereof, or ammunition of any applicable"
            " commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.\n"
        ) in case_email.body

    def test_create_sil_constabulary_email(self, ilb_admin_client, fa_sil_app_submitted):
        app = fa_sil_app_submitted

        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "import"))
        app.refresh_from_db()

        case_email = create_case_email(
            app, EmailTypes.CONSTABULARY_CASE_EMAIL, cc=["cc_address@example.com"]  # /PS-IGNORE
        )

        assert case_email.to is None
        assert case_email.cc_address_list == ["cc_address@example.com"]  # /PS-IGNORE
        assert case_email.subject == "Import Licence RFD Enquiry"

        assert (
            "\n111 x Section 1 goods to which Section 1 of the Firearms Act 1968, as amended, applies.\n"
            "222 x Section 2 goods to which Section 2 of the Firearms Act 1968, as amended, applies.\n"
            "333 x Section 5 goods to which Section 5(A) section 5 subsection of the Firearms Act 1968, as amended, applies.\n"
            "444 x Section 58 obsoletes goods chambered in the obsolete calibre Obsolete calibre value to which "
            "Section 58(2) of the Firearms Act 1968, as amended, applies.\n"
            "555 x Section 58 other goods to which Section 58(2) of the Firearms Act 1968, as amended, applies.\n"
        ) in case_email.body

    def test_create_sanctions_email(self, sanctions_app_submitted):
        app = sanctions_app_submitted
        self.ilb_admin_client.post(CaseURLS.take_ownership(app.pk, "import"))
        app.refresh_from_db()
        case_email = create_case_email(app, EmailTypes.SANCTIONS_CASE_EMAIL)

        assert case_email.to is None
        assert case_email.cc_address_list is None
        assert case_email.subject == "Import Sanctions and Adhoc Licence"
        assert "\n1000 x Test Goods\n56.78 x More Commoditites\n" in case_email.body
