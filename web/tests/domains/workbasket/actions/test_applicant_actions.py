import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from web.domains.case.services import document_pack
from web.domains.case.shared import ImpExpStatus
from web.domains.workbasket.actions import ActionConfig
from web.domains.workbasket.actions.applicant_actions import (
    ClearApplicationAction,
    ClearIssuedDocumentsAction,
    EditECILApplicationAction,
    ShowWelcomeMessageAction,
    SubmitVariationUpdateAction,
    ViewApplicationAction,
    ViewIssuedDocumentsAction,
    WithdrawApplicationAction,
)
from web.models import Task, User, VariationRequest, WoodQuotaApplication


class TestApplicantActions:
    user: User
    app: WoodQuotaApplication
    TT = Task.TaskType
    ST = ImpExpStatus

    @pytest.fixture(autouse=True)
    def setup(self, importer_one_contact, importer):
        self.user = importer_one_contact

        # Set the minimum required fields.
        self.app = WoodQuotaApplication(pk=1, importer=importer)

    def test_view_application_action_is_shown(self):
        # setup
        self.app.active_tasks = []

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
            config = ActionConfig(user=self.user, case_type="import", application=self.app)
            action = ViewApplicationAction.from_config(config)

            if status in shown_statuses:
                assert action.show_link()
                wb_action = action.get_workbasket_actions()[0]
                assert wb_action.name == "View Application"

            else:
                assert not action.show_link()

    def test_withdraw_application_action(self):
        # setup
        self.app.active_tasks = []

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
                config = ActionConfig(user=self.user, case_type="import", application=self.app)
                action = WithdrawApplicationAction.from_config(config)

                if status in valid_statuses:
                    assert action.show_link()
                    wb_action = action.get_workbasket_actions()[0]
                    expected_name = "Pending Withdrawal" if has_withdrawal else "Withdraw"

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
        wood_app_submitted.active_tasks = [self.TT.VR_REQUEST_CHANGE]

        # test
        config = ActionConfig(user=self.user, case_type="import", application=wood_app_submitted)
        action = SubmitVariationUpdateAction.from_config(config)

        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Submit Update"

    def test_submit_variation_request_update_action_not_shown(self):
        # setup
        self.app.status = self.ST.VARIATION_REQUESTED
        self.app.active_tasks = []

        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = SubmitVariationUpdateAction.from_config(config)

        assert not action.show_link()

    def test_clear_application_action_is_shown(self, ilb_admin_user):
        self.app.active_tasks = []

        for status in self.ST:
            self.app.status = status

            # test
            config = ActionConfig(user=self.user, case_type="import", application=self.app)
            action = ClearApplicationAction.from_config(config)

            if status in [self.ST.COMPLETED, self.ST.REVOKED]:
                assert action.show_link()
                wb_action = action.get_workbasket_actions()[0]
                assert wb_action.name == "Clear"

            else:
                assert not action.show_link()

    def test_view_issued_documents_is_shown(self, completed_sil_app):
        completed_sil_app.active_tasks = []

        config = ActionConfig(user=self.user, case_type="import", application=completed_sil_app)
        action = ViewIssuedDocumentsAction.from_config(config)

        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Issued Documents"
        assert wb_action.section_label.startswith("Documents Issued ")

    def test_view_issued_documents_not_shown(self, completed_sil_app, importer_one_contact):
        completed_sil_app.active_tasks = []

        # Use the wood app in `self.app` to show it not showing
        self.app.active_tasks = []
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewIssuedDocumentsAction.from_config(config)

        assert not action.show_link()

        # Test completed app is no longer shown
        pack = document_pack.pack_active_get(completed_sil_app)
        document_pack.pack_workbasket_remove_pack(
            completed_sil_app, importer_one_contact, pack_pk=pack.pk
        )

        config = ActionConfig(user=self.user, case_type="import", application=completed_sil_app)
        action = ViewIssuedDocumentsAction.from_config(config)

        assert not action.show_link()

    def test_clear_issued_documents_is_shown(self, completed_sil_app):
        completed_sil_app.active_tasks = []

        config = ActionConfig(user=self.user, case_type="import", application=completed_sil_app)
        action = ClearIssuedDocumentsAction.from_config(config)

        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Clear"
        assert wb_action.section_label.startswith("Documents Issued ")

    def test_clear_issued_documents_not_shown(self, completed_sil_app, importer_one_contact):
        self.app.active_tasks = []
        completed_sil_app.active_tasks = []

        # Use the wood app in `self.app` to show it not showing
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ClearIssuedDocumentsAction.from_config(config)

        assert not action.show_link()

        # Test completed app is no longer shown
        pack = document_pack.pack_active_get(completed_sil_app)
        document_pack.pack_workbasket_remove_pack(
            completed_sil_app, importer_one_contact, pack_pk=pack.pk
        )

        config = ActionConfig(user=self.user, case_type="import", application=completed_sil_app)
        action = ClearIssuedDocumentsAction.from_config(config)

        assert not action.show_link()

    def test_show_welcome_message_not_shown(self):
        action = ShowWelcomeMessageAction(self.user)

        assert not action.show_link()

    def test_show_welcome_message_shown(self):
        self.user.show_welcome_message = True
        self.user.save()

        action = ShowWelcomeMessageAction(self.user)

        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Welcome Message"
        assert wb_action.section_label == "Welcome & Introduction"

        wb_action = action.get_workbasket_actions()[1]
        assert wb_action.name == "Clear From Workbasket"
        assert wb_action.section_label == "Welcome & Introduction"


def test_edit_ecil_application_action(cfs_app_in_progress, exporter_one_contact):
    cfs_app_in_progress.active_tasks = [Task.TaskType.PREPARE]

    # test exporter contact can't see it initially
    config = ActionConfig(
        user=exporter_one_contact, case_type="export", application=cfs_app_in_progress
    )
    action = EditECILApplicationAction.from_config(config)

    assert not action.show_link()

    # Give the exporter_one_contact the correct prototype permission
    group = Group.objects.get(name="ECIL Prototype User")
    exporter_one_contact.groups.add(group)

    # Only way to clear permission checking cache in same test.
    exporter_one_contact = User.objects.get(pk=exporter_one_contact.pk)

    config = ActionConfig(
        user=exporter_one_contact, case_type="export", application=cfs_app_in_progress
    )
    action = EditECILApplicationAction.from_config(config)
    assert action.show_link()

    wb_action = action.get_workbasket_actions()[0]
    assert wb_action.name == "Resume"
    assert wb_action.section_label == "ECIL Prototype"
    assert wb_action.url == reverse(
        "ecil:export-cfs:application-reference", kwargs={"application_pk": cfs_app_in_progress.pk}
    )
