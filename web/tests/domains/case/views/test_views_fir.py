from typing import TYPE_CHECKING

from pytest_django.asserts import assertContains, assertTemplateUsed

from web.tests.helpers import CaseURLS

if TYPE_CHECKING:
    from django.test.client import Client

    from web.models import WoodQuotaApplication


def test_manage_update_requests_get(
    icms_admin_client: "Client", wood_app_submitted: "WoodQuotaApplication"
) -> None:
    resp = icms_admin_client.get(CaseURLS.manage_firs(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Further Information Requests")
    assertTemplateUsed(resp, "web/domains/case/manage/list-firs.html")

    assert resp.context["firs"].count() == 0


# def test_manage_update_requests_post():
#     # TODO: Add test for sending an update request
#     ...
