from django.http import HttpResponse
from django.test.client import Client
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.models import (
    DFLApplication,
    ExportApplication,
    ImportApplication,
    Task,
    User,
    VariationRequest,
    WoodQuotaApplication,
)
from web.tests.helpers import CaseURLS, add_variation_request_to_app


def test_wood_quota_prepare_response_get(
    ilb_admin_client: Client, wood_app_submitted: WoodQuotaApplication
) -> None:
    resp = ilb_admin_client.get(CaseURLS.prepare_response(wood_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(resp, "Wood (Quota) - Response Preparation")
    assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-wood-quota-response.html")


# TODO: Add test for each application type as response prep is different for each


def test_fa_dfl_prepare_response_get(
    ilb_admin_client: Client, fa_dfl_app_submitted: DFLApplication
) -> None:
    resp = ilb_admin_client.get(CaseURLS.prepare_response(fa_dfl_app_submitted.pk))
    assert resp.status_code == 200

    assertContains(
        resp, "Firearms and Ammunition (Deactivated Firearms Licence) - Response Preparation"
    )
    assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-fa-dfl-response.html")


def test_export_variation_request_cannot_edit_decision(
    ilb_admin_client: Client, ilb_admin_user: User, completed_cfs_app: ExportApplication
) -> None:
    response = _setup_app_with_variation_request(
        completed_cfs_app, ilb_admin_client, ilb_admin_user, "export"
    )
    assertNotContains(response, '<input class="primary-button button" type="submit" value="Save"/>')


def test_import_variation_request_can_edit_decision(
    ilb_admin_client: Client, ilb_admin_user: User, completed_dfl_app: ImportApplication
) -> None:
    response = _setup_app_with_variation_request(
        completed_dfl_app, ilb_admin_client, ilb_admin_user, "import"
    )
    assertContains(response, '<input class="primary-button button" type="submit" value="Save"/>')


def _setup_app_with_variation_request(
    app: ImpOrExp, client: Client, ilb_admin_user: User, case_type: str
) -> HttpResponse:
    document_pack.pack_draft_create(app)
    add_variation_request_to_app(app, ilb_admin_user, status=VariationRequest.Statuses.OPEN)
    app.status = ImpExpStatus.VARIATION_REQUESTED
    app.save()
    Task.objects.create(process=app, task_type=Task.TaskType.PROCESS, previous=None)
    client.post(CaseURLS.take_ownership(app.pk, case_type=case_type))
    response = client.get(CaseURLS.prepare_response(app.pk, case_type=case_type))
    assert response.status_code == 200
    return response


# def test_prepare_response_post():
#     # TODO: Add test for approving an application
#     # TODO: Add test for rejecting an application
#     ...
