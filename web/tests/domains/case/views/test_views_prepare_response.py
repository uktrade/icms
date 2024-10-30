from http import HTTPStatus

import pytest
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
from web.flow.models import ProcessTypes
from web.models import (
    CertificateOfFreeSaleApplication,
    CertificateOfGoodManufacturingPracticeApplication,
    CertificateOfManufactureApplication,
    DerogationsApplication,
    DFLApplication,
    ExportApplication,
    ImportApplication,
    OpenIndividualLicenceApplication,
    OutwardProcessingTradeApplication,
    PriorSurveillanceApplication,
    SILApplication,
    Task,
    TextilesApplication,
    User,
    VariationRequest,
    WoodQuotaApplication,
)
from web.tests.auth import AuthTestCase
from web.tests.helpers import CaseURLS, add_variation_request_to_app


class TestPrepareResponseView(AuthTestCase):

    def test_wood_quota_prepare_response_get(
        self, wood_app_submitted: WoodQuotaApplication
    ) -> None:
        resp = self.ilb_admin_client.get(CaseURLS.prepare_response(wood_app_submitted.pk))
        assert resp.status_code == HTTPStatus.OK

        assertContains(resp, "Wood (Quota) - Response Preparation")
        assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-wood-quota-response.html")

    def test_fa_dfl_prepare_response_get(self, fa_dfl_app_submitted: DFLApplication) -> None:
        resp = self.ilb_admin_client.get(CaseURLS.prepare_response(fa_dfl_app_submitted.pk))
        assert resp.status_code == HTTPStatus.OK

        assertContains(
            resp, "Firearms and Ammunition (Deactivated Firearms Licence) - Response Preparation"
        )
        assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-fa-dfl-response.html")

    def test_fa_oil_prepare_response_get(
        self, fa_oil_app_submitted: OpenIndividualLicenceApplication
    ) -> None:
        resp = self.ilb_admin_client.get(CaseURLS.prepare_response(fa_oil_app_submitted.pk))
        assert resp.status_code == HTTPStatus.OK

        assertContains(
            resp, "Firearms and Ammunition (Open Individual Import Licence) - Response Preparation"
        )
        assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-fa-oil-response.html")

    def test_fa_sil_prepare_response_get(self, fa_sil_app_submitted: SILApplication) -> None:
        resp = self.ilb_admin_client.get(CaseURLS.prepare_response(fa_sil_app_submitted.pk))
        assert resp.status_code == HTTPStatus.OK

        assertContains(resp, "Firearms and Ammunition (Specific Individual Import Licence)")
        assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-fa-sil-response.html")

    def test_derogations_prepare_response_get(
        self, derogation_app_submitted: DerogationsApplication
    ) -> None:
        resp = self.ilb_admin_client.get(CaseURLS.prepare_response(derogation_app_submitted.pk))
        assert resp.status_code == HTTPStatus.OK

        assertContains(resp, "Derogation from Sanctions Import Ban")
        assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-derogations-response.html")

    def test_opt_prepare_response_get(
        self, opt_app_submitted: OutwardProcessingTradeApplication
    ) -> None:
        resp = self.ilb_admin_client.get(CaseURLS.prepare_response(opt_app_submitted.pk))
        assert resp.status_code == HTTPStatus.OK

        assertContains(resp, "Outward Processing Trade")
        assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-opt-response.html")

    def test_com_prepare_response_get(
        self, com_app_submitted: CertificateOfManufactureApplication
    ) -> None:
        resp = self.ilb_admin_client.get(
            CaseURLS.prepare_response(com_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == HTTPStatus.OK

        assertContains(resp, "Certificate of Manufacture")
        assertTemplateUsed(resp, "web/domains/case/export/manage/prepare-com-response.html")

    def test_gmp_prepare_response_get(
        self, gmp_app_submitted: CertificateOfGoodManufacturingPracticeApplication
    ) -> None:
        resp = self.ilb_admin_client.get(
            CaseURLS.prepare_response(gmp_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == HTTPStatus.OK

        assertContains(resp, "Certificate of Good Manufacturing Practice")
        assertTemplateUsed(resp, "web/domains/case/export/manage/prepare-gmp-response.html")

    def test_cfs_prepare_response_get(
        self, cfs_app_submitted: CertificateOfFreeSaleApplication
    ) -> None:
        resp = self.ilb_admin_client.get(
            CaseURLS.prepare_response(cfs_app_submitted.pk, case_type="export")
        )
        assert resp.status_code == HTTPStatus.OK

        assertContains(resp, "Certificate of Free Sale")
        assertTemplateUsed(resp, "web/domains/case/export/manage/prepare-cfs-response.html")

    def test_textiles_prepare_response_get(
        self, textiles_app_submitted: TextilesApplication
    ) -> None:
        resp = self.ilb_admin_client.get(CaseURLS.prepare_response(textiles_app_submitted.pk))
        assert resp.status_code == HTTPStatus.OK

        assertContains(resp, "Textiles (Quota)")
        assertTemplateUsed(
            resp, "web/domains/case/import/manage/prepare-textiles-quota-response.html"
        )

    def test_sps_prepare_response_get(
        self, sps_app_submitted: PriorSurveillanceApplication
    ) -> None:
        resp = self.ilb_admin_client.get(CaseURLS.prepare_response(sps_app_submitted.pk))
        assert resp.status_code == HTTPStatus.OK

        assertContains(resp, "Prior Surveillance")
        assertTemplateUsed(resp, "web/domains/case/import/manage/prepare-sps-response.html")

    def test_prepare_response_invalid_case_type_get(
        self, fa_sil_app_submitted: SILApplication
    ) -> None:
        with pytest.raises(NotImplementedError, match="Unknown case_type access"):
            self.ilb_admin_client.get(
                CaseURLS.prepare_response(fa_sil_app_submitted.pk, case_type="access")
            )

    def test_prepare_response_invalid_process_type_get(
        self, fa_sil_app_submitted: SILApplication
    ) -> None:
        """Changing the process type to cause an error"""
        fa_sil_app_submitted.process_type = ProcessTypes.FIR
        fa_sil_app_submitted.save()
        with pytest.raises(
            NotImplementedError,
            match="Application process type 'FurtherInformationRequest' haven't been configured yet",
        ):
            self.ilb_admin_client.get(CaseURLS.prepare_response(fa_sil_app_submitted.pk))

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
        assert response.status_code == HTTPStatus.OK
        return response

    def test_get_licence_for_completed_approved_application(
        self, completed_dfl_app: DFLApplication
    ) -> None:
        _license = get_licence_for_application(completed_dfl_app)
        assert _license.status == DocumentPackBase.Status.ACTIVE

    def test_get_licence_for_submitted_application(
        self, fa_dfl_app_submitted: DFLApplication
    ) -> None:
        _license = get_licence_for_application(fa_dfl_app_submitted)
        assert _license.status == DocumentPackBase.Status.DRAFT

    def test_get_licence_for_revoked_application(self, completed_dfl_app: DFLApplication) -> None:
        completed_dfl_app.status = ImportApplication.Statuses.REVOKED
        completed_dfl_app.save()
        document_pack.pack_active_revoke(completed_dfl_app, "Test revoke reason", False)
        _license = get_licence_for_application(completed_dfl_app)
        assert _license.status == DocumentPackBase.Status.REVOKED

    def test_get_licence_for_rejected_application(
        self, complete_rejected_app: SILApplication
    ) -> None:
        _license = get_licence_for_application(complete_rejected_app)
        assert _license is None
