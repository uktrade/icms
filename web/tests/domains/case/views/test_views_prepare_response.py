from typing import TYPE_CHECKING

from pytest_django.asserts import assertContains, assertTemplateUsed

from web.tests.helpers import CaseURLS

if TYPE_CHECKING:
    from django.test.client import Client

    from web.models import DFLApplication, WoodQuotaApplication


def test_wood_quota_prepare_response_get(
    ilb_admin_client: "Client", wood_app_submitted: "WoodQuotaApplication"
) -> None:
    resp = ilb_admin_client.get(CaseURLS.prepare_response(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Response Preparation")
    assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-wood-quota-response.html")


# TODO: Add test for each application type as response prep is different for each


def test_fa_dfl_prepare_response_get(
    ilb_admin_client: "Client", fa_dfl_app_submitted: "DFLApplication"
) -> None:
    resp = ilb_admin_client.get(CaseURLS.prepare_response(fa_dfl_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(
        resp, "Firearms and Ammunition (Deactivated Firearms Licence) - Response Preparation"
    )
    assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-fa-dfl-response.html")


# def test_prepare_response_post():
#     # TODO: Add test for approving an application
#     # TODO: Add test for rejecting an application
#     ...
