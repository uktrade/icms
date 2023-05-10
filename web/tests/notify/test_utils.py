import pytest

from web.models import AlternativeEmail, PersonalEmail
from web.notify.notify import utils
from web.tests.domains.user.factory import UserFactory
from web.tests.helpers import CaseURLS


@pytest.mark.django_db
def test_get_notification_emails():
    user = UserFactory()
    PersonalEmail(
        user=user, email="email@example.com", portal_notifications=True  # /PS-IGNORE
    ).save()
    PersonalEmail(
        user=user, email="second_email@example.com", portal_notifications=False  # /PS-IGNORE
    ).save()
    AlternativeEmail(
        user=user, email="alternative@example.com", portal_notifications=False  # /PS-IGNORE
    ).save()
    AlternativeEmail(
        user=user,
        email="second_alternative@example.com",  # /PS-IGNORE
        portal_notifications=True,
    ).save()
    emails = utils.get_notification_emails(user)
    assert len(emails) == 2
    assert emails[0] == "email@example.com"  # /PS-IGNORE
    assert emails[1] == "second_alternative@example.com"  # /PS-IGNORE


def test_create_gmp_case_beis_email(icms_admin_client, gmp_app_submitted):
    app = gmp_app_submitted
    icms_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))
    app.refresh_from_db()

    attachments = app.supporting_documents.filter(is_active=True)
    case_email = utils.create_case_email(
        app,
        "CA_BEIS_EMAIL",
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


def test_create_cfs_case_hse_email(icms_admin_client, cfs_app_submitted):
    app = cfs_app_submitted

    icms_admin_client.post(CaseURLS.take_ownership(app.pk, "export"))
    app.refresh_from_db()

    case_email = utils.create_case_email(
        app, "CA_HSE_EMAIL", "to_address@example.com"  # /PS-IGNORE
    )

    assert case_email.to == "to_address@example.com"  # /PS-IGNORE
    assert case_email.subject == "Biocidal Product Enquiry"
    assert "The application is for the following biocidal products" in case_email.body


def test_create_dfl_constabulary_email(icms_admin_client, fa_dfl_app_submitted):
    app = fa_dfl_app_submitted

    icms_admin_client.post(CaseURLS.take_ownership(app.pk, "import"))
    app.refresh_from_db()

    case_email = utils.create_case_email(
        app, "IMA_CONSTAB_EMAIL", cc=["cc_address@example.com"]  # /PS-IGNORE
    )

    assert case_email.to is None
    assert case_email.cc_address_list == ["cc_address@example.com"]  # /PS-IGNORE
    assert case_email.subject == "Import Licence RFD Enquiry"
    assert "\ngoods_description value\n" in case_email.body


def test_create_oil_constabulary_email(icms_admin_client, fa_oil_app_submitted):
    app = fa_oil_app_submitted

    icms_admin_client.post(CaseURLS.take_ownership(app.pk, "import"))
    app.refresh_from_db()

    case_email = utils.create_case_email(
        app, "IMA_CONSTAB_EMAIL", cc=["cc_address@example.com"]  # /PS-IGNORE
    )

    assert case_email.to is None
    assert case_email.cc_address_list == ["cc_address@example.com"]  # /PS-IGNORE
    assert case_email.subject == "Import Licence RFD Enquiry"

    assert (
        "\nFirearms, component parts thereof, or ammunition of any applicable"
        " commodity code, other than those falling under Section 5 of the Firearms Act 1968 as amended.\n"
    ) in case_email.body


def test_create_sil_constabulary_email(icms_admin_client, fa_sil_app_submitted):
    app = fa_sil_app_submitted

    icms_admin_client.post(CaseURLS.take_ownership(app.pk, "import"))
    app.refresh_from_db()

    case_email = utils.create_case_email(
        app, "IMA_CONSTAB_EMAIL", cc=["cc_address@example.com"]  # /PS-IGNORE
    )

    assert case_email.to is None
    assert case_email.cc_address_list == ["cc_address@example.com"]  # /PS-IGNORE
    assert case_email.subject == "Import Licence RFD Enquiry"

    assert (
        "\n111 x Section 1 goods to which Section 1 of the Firearms Act 1968, as amended, applies.\n"
        "222 x Section 2 goods to which Section 2 of the Firearms Act 1968, as amended, applies.\n"
        "333 x Section 5 goods to which Section section 5 subsection of the Firearms Act 1968, as amended, applies.\n"
        "444 x Section 58 obsoletes goods chambered in the obsolete calibre Obsolete calibre value to which "
        "Section 58(2) of the Firearms Act 1968, as amended, applies.\n"
        "555 x Section 58 other goods to which Section 58(2) of the Firearms Act 1968, as amended, applies.\n"
    ) in case_email.body


def test_create_sanctions_email(icms_admin_client, sanctions_app_submitted):
    app = sanctions_app_submitted
    icms_admin_client.post(CaseURLS.take_ownership(app.pk, "import"))
    app.refresh_from_db()
    case_email = utils.create_case_email(app, "IMA_SANCTION_EMAIL")

    assert case_email.to is None
    assert case_email.cc_address_list is None
    assert case_email.subject == "Import Sanctions and Adhoc Licence"
    assert "\n1000 x Test Goods\n56.78 x More Commoditites\n" in case_email.body
