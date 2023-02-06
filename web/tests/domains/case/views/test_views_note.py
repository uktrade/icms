from typing import TYPE_CHECKING

from pytest_django.asserts import assertContains, assertTemplateUsed

from web.domains.case.models import CASE_NOTE_DRAFT
from web.tests.helpers import CaseURLS

if TYPE_CHECKING:
    from django.test.client import Client

    from web.domains.case._import.wood.models import WoodQuotaApplication


def test_manage_update_requests_get(
    icms_admin_client: "Client", wood_app_submitted: "WoodQuotaApplication", test_icms_admin_user
) -> None:
    wood_app_submitted.case_notes.create(status=CASE_NOTE_DRAFT, created_by=test_icms_admin_user)

    resp = icms_admin_client.get(CaseURLS.list_notes(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Notes")
    assertContains(resp, "Case Notes")
    assertTemplateUsed(resp, "web/domains/case/manage/list-notes.html")

    assert resp.context["notes"].count() == 1
