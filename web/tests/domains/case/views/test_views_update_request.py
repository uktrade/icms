from typing import TYPE_CHECKING

from pytest_django.asserts import assertContains, assertTemplateUsed

from web.tests.helpers import CaseURLS

if TYPE_CHECKING:
    from django.test.client import Client

    from web.domains.case._import.wood.models import WoodQuotaApplication


def test_list_update_requests_get(
    icms_admin_client: "Client", wood_app_submitted: "WoodQuotaApplication"
) -> None:
    resp = icms_admin_client.get(CaseURLS.list_update_requests(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Update Requests")
    assertTemplateUsed(resp, "web/domains/case/manage/list-update-requests.html")

    assert resp.context["previous_update_requests"].count() == 0
    assert resp.context["update_request"] is None


# def test_manage_update_requests_post():
#     # TODO: Add test for sending an update request
#     ...
