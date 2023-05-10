from typing import TYPE_CHECKING

from pytest_django.asserts import assertContains, assertTemplateUsed

from web.tests.helpers import CaseURLS

if TYPE_CHECKING:
    from django.test.client import Client

    from web.models import DFLApplication


def test_manage_constabulary_emails_get(
    ilb_admin_client: "Client", fa_dfl_app_submitted: "DFLApplication"
) -> None:
    resp = ilb_admin_client.get(CaseURLS.manage_case_emails(fa_dfl_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Manage Emails")
    assertTemplateUsed(resp, "web/domains/case/manage/case-emails.html")

    assert resp.context["case_emails"].count() == 0

    # Firearms applications display constabulary emails
    assert resp.context["info_email"] == (
        "This screen is used to email relevant constabularies. You may attach multiple"
        " firearms certificates to a single email. You can also record responses from the constabulary."
    )
