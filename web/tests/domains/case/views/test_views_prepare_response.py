from django.conf import settings
from django.http import HttpResponse
from django.test import override_settings
from django.test.client import Client
from pytest_django.asserts import assertContains, assertNotContains, assertTemplateUsed

from web.domains.case.models import DocumentPackBase
from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.domains.case.views.views_prepare_response import get_licence_for_application
from web.models import (
    DFLApplication,
    ExportApplication,
    ImportApplication,
    Task,
    User,
    VariationRequest,
    WoodQuotaApplication,
)
from web.tests.auth import AuthTestCase
from web.tests.helpers import CaseURLS, add_variation_request_to_app


class TestPrepareResponseView(AuthTestCase):
    # TODO: ICMSLST-2090 - Add missing prep response unittests
    # Add test for each application type as response prep is different for each
    # Add test for rejecting and approving an application

    def test_wood_quota_prepare_response_get(
        self, wood_app_submitted: WoodQuotaApplication
    ) -> None:
        resp = self.ilb_admin_client.get(CaseURLS.prepare_response(wood_app_submitted.pk))
        assert resp.status_code == 200

        assertContains(resp, "Wood (Quota) - Response Preparation")
        assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-wood-quota-response.html")

    def test_fa_dfl_prepare_response_get(self, fa_dfl_app_submitted: DFLApplication) -> None:
        resp = self.ilb_admin_client.get(CaseURLS.prepare_response(fa_dfl_app_submitted.pk))
        assert resp.status_code == 200

        assertContains(
            resp, "Firearms and Ammunition (Deactivated Firearms Licence) - Response Preparation"
        )
        assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-fa-dfl-response.html")

    @override_settings(TEMPLATES=settings.STRICT_TEMPLATES)
    def test_export_variation_request_cannot_edit_decision(
        self, completed_cfs_app: ExportApplication
    ) -> None:
        response = self._setup_app_with_variation_request(
            completed_cfs_app, self.ilb_admin_client, self.ilb_admin_user, "export"
        )
        assertNotContains(
            response, '<input class="primary-button button" type="submit" value="Save"/>'
        )
        assert "licence" not in response.context

    def test_import_variation_request_can_edit_decision(
        self, completed_dfl_app: ImportApplication
    ) -> None:
        response = self._setup_app_with_variation_request(
            completed_dfl_app, self.ilb_admin_client, self.ilb_admin_user, "import"
        )

        _licence = response.context.get("licence")
        assert _licence is not None
        assert response.context["readonly_view"] is False
        assertContains(
            response, '<input class="primary-button button" type="submit" value="Save"/>'
        )
        assertContains(response, "<th>Actions</th>")

    def test_import_variation_request_refused_cannot_see_actions(
        self, completed_dfl_app: ImportApplication
    ) -> None:
        self._setup_app_with_variation_request(
            completed_dfl_app, self.ilb_admin_client, self.ilb_admin_user, "import"
        )
        completed_dfl_app.refresh_from_db()
        completed_dfl_app.variation_decision = completed_dfl_app.REFUSE
        completed_dfl_app.save()

        response = self.ilb_admin_client.get(CaseURLS.prepare_response(completed_dfl_app.pk))

        _licence = response.context.get("licence")
        assert _licence is not None
        assert response.context["readonly_view"] is False
        assertContains(
            response, '<input class="primary-button button" type="submit" value="Save"/>'
        )
        assertNotContains(response, "<th>Actions</th>")

    def _setup_app_with_variation_request(
        self, app: ImpOrExp, client: Client, ilb_admin_user: User, case_type: str
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

    def test_get_licence_for_completed_approved_application(self, completed_dfl_app):
        _license = get_licence_for_application(completed_dfl_app)
        assert _license.status == DocumentPackBase.Status.ACTIVE

    def test_get_licence_for_submitted_application(self, fa_dfl_app_submitted):
        _license = get_licence_for_application(fa_dfl_app_submitted)
        assert _license.status == DocumentPackBase.Status.DRAFT

    def test_get_licence_for_revoked_application(self, completed_dfl_app):
        completed_dfl_app.status = ImportApplication.Statuses.REVOKED
        completed_dfl_app.save()
        document_pack.pack_active_revoke(completed_dfl_app, "Test revoke reason", False)
        _license = get_licence_for_application(completed_dfl_app)
        assert _license.status == DocumentPackBase.Status.REVOKED

    def test_get_licence_for_rejected_application(self, complete_rejected_app):
        _license = get_licence_for_application(complete_rejected_app)
        assert _license is None
