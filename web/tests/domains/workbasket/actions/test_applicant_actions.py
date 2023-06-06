import pytest
from django.utils import timezone

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.workbasket.actions.applicant_actions import (
    ClearIssuedDocumentsAction,
    SubmitVariationUpdateAction,
    ViewApplicationAction,
    ViewIssuedDocumentsAction,
    WithdrawApplicationAction,
)
from web.domains.workbasket.actions.shared_actions import ClearApplicationAction
from web.models import Task, User, VariationRequest, WoodQuotaApplication


class TestApplicantActions:
    user: User
    app: WoodQuotaApplication
    TT = Task.TaskType
    ST = ImpExpStatus

    @pytest.fixture(autouse=True)
    def setup(self, importer_one_contact):
        self.user = importer_one_contact

        # set pk as it's the minimum needed to craft the url
        self.app = WoodQuotaApplication(pk=1)

    def test_view_application_action_is_shown(self):
        # setup
        active_tasks = []

        # Statuses when the View Application link should show
        shown_statuses = [
            self.ST.SUBMITTED,
            self.ST.PROCESSING,
            self.ST.VARIATION_REQUESTED,
            self.ST.COMPLETED,
            self.ST.REVOKED,
        ]

        for status in self.ST:
            self.app.status = status

            # test
            action = ViewApplicationAction(
                self.user, "import", self.app, active_tasks, False, True, False
            )

            if status in shown_statuses:
                assert action.show_link()
                wb_action = action.get_workbasket_actions()[0]
                assert wb_action.name == "View Application"

            else:
                assert not action.show_link()

    def test_withdraw_application_action(self):
        # setup
        active_tasks = []

        valid_statuses = [
            ImpExpStatus.SUBMITTED,
            ImpExpStatus.PROCESSING,
            ImpExpStatus.VARIATION_REQUESTED,
        ]

        for status in self.ST:
            for has_withdrawal in (True, False):
                self.app.status = status
                self.app.annotation_has_withdrawal = has_withdrawal

                # test
                action = WithdrawApplicationAction(
                    self.user, "import", self.app, active_tasks, False, True, False
                )

                if status in valid_statuses:
                    assert action.show_link()
                    wb_action = action.get_workbasket_actions()[0]
                    expected_name = "Pending Withdrawal" if has_withdrawal else "Request Withdrawal"

                    assert wb_action.name == expected_name
                    assert wb_action.section_label == "Application Submitted"

                else:
                    assert not action.show_link()

    def test_submit_variation_request_update_action_is_shown(self, wood_app_submitted):
        # setup
        wood_app_submitted.variation_requests.create(
            status=VariationRequest.Statuses.OPEN,
            what_varied="Dummy what_varied",
            why_varied="Dummy why_varied",
            when_varied=timezone.now().date(),
            requested_by=self.user,
        )
        wood_app_submitted.status = self.ST.VARIATION_REQUESTED
        active_tasks = [self.TT.VR_REQUEST_CHANGE]

        # test
        action = SubmitVariationUpdateAction(
            self.user, "import", wood_app_submitted, active_tasks, False, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Submit Update"

    def test_submit_variation_request_update_action_not_shown(self):
        # setup
        self.app.status = self.ST.VARIATION_REQUESTED
        active_tasks = []

        action = SubmitVariationUpdateAction(
            self.user, "import", self.app, active_tasks, False, True, False
        )
        assert not action.show_link()

    def test_clear_application_action_is_shown(self, ilb_admin_user):
        active_tasks = []
        for status in self.ST:
            self.app.status = status

            # test
            action = ClearApplicationAction(
                self.user, "import", self.app, active_tasks, False, True, False
            )

            if status in [self.ST.COMPLETED, self.ST.REVOKED]:
                assert action.show_link()
                wb_action = action.get_workbasket_actions()[0]
                assert wb_action.name == "Clear"

            else:
                assert not action.show_link()

    def test_view_issued_documents_is_shown(self, completed_sil_app):
        active_tasks = []
        action = ViewIssuedDocumentsAction(
            self.user, "import", completed_sil_app, active_tasks, False, True, False
        )

        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Issued Documents"
        assert wb_action.section_label.startswith("Documents Issued ")

    def test_view_issued_documents_not_shown(self, completed_sil_app):
        active_tasks = []

        # Use the wood app in `self.app` to show it not showing
        action = ViewIssuedDocumentsAction(
            self.user, "import", self.app, active_tasks, False, True, False
        )
        assert not action.show_link()

        # Test completed app is no longer shown
        licence = document_pack.pack_active_get(completed_sil_app)
        licence.show_in_workbasket = False
        licence.save()

        action = ViewIssuedDocumentsAction(
            self.user, "import", completed_sil_app, active_tasks, False, True, False
        )
        assert not action.show_link()

    def test_clear_issued_documents_is_shown(self, completed_sil_app):
        active_tasks = []
        action = ClearIssuedDocumentsAction(
            self.user, "import", completed_sil_app, active_tasks, False, True, False
        )

        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Clear"
        assert wb_action.section_label.startswith("Documents Issued ")

    def test_clear_issued_documents_not_shown(self, completed_sil_app):
        active_tasks = []

        # Use the wood app in `self.app` to show it not showing
        action = ClearIssuedDocumentsAction(
            self.user, "import", self.app, active_tasks, False, True, False
        )
        assert not action.show_link()

        # Test completed app is no longer shown
        licence = document_pack.pack_active_get(completed_sil_app)
        licence.show_in_workbasket = False
        licence.save()

        action = ClearIssuedDocumentsAction(
            self.user, "import", completed_sil_app, active_tasks, False, True, False
        )
        assert not action.show_link()
