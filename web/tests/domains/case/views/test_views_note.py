from django.test.client import Client
from pytest_django.asserts import assertContains, assertTemplateUsed

from web.models import WoodQuotaApplication
from web.tests.helpers import CaseURLS


def test_manage_update_requests_get(
    ilb_admin_client: Client, wood_app_submitted: WoodQuotaApplication, ilb_admin_user
) -> None:
    wood_app_submitted.case_notes.create(created_by=ilb_admin_user)

    resp = ilb_admin_client.get(CaseURLS.list_notes(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Notes")
    assertContains(resp, "Case Notes")
    assertTemplateUsed(resp, "web/domains/case/manage/list-notes.html")

    assert resp.context["notes"].count() == 1
