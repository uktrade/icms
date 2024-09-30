import pytest

from web.domains.case.shared import ImpExpStatus
from web.domains.workbasket.actions import ActionConfig, get_workbasket_admin_sections
from web.domains.workbasket.actions.ilb_admin_actions import (
    AuthoriseDocumentsAction,
    CancelAuthorisationAction,
    CheckCaseDocumentGenerationAction,
    ManageApplicationAction,
    ManageWithdrawApplicationAction,
    RecreateCaseDocumentsAction,
    TakeOwnershipAction,
    ViewApplicationCaseAction,
)
from web.mail.constants import CaseEmailCodes
from web.models import Task, User, WoodQuotaApplication

ST = ImpExpStatus
TT = Task.TaskType


class TestAdminActions:
    user: User
    app: WoodQuotaApplication

    @pytest.fixture(autouse=True)
    def setup(self, ilb_admin_user, importer):
        self.user = ilb_admin_user

        # Set the minimum required fields.
        self.app = WoodQuotaApplication(pk=1, importer=importer)
        self.app.annotation_open_fir_pks = []
        self.app.open_case_emails = []

    def test_view_case_action_is_shown(self):
        """A freshly submitted application (no case_owner yet)"""
        # setup
        self.app.status = ST.SUBMITTED
        self.app.case_owner = None
        self.app.active_tasks = []

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_is_not_shown_app_processing_another_admin(self):
        """An application being processed by another ilb admin"""
        # setup
        self.app.status = ST.PROCESSING
        self.app.case_owner = User(first_name="Another", last_name="User")
        self.app.active_tasks = []

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert not action.show_link()

    def test_view_case_action_is_shown_when_authorised(self):
        # setup
        self.app.status = ST.PROCESSING
        self.app.case_owner = self.user
        self.app.active_tasks = [Task.TaskType.AUTHORISE]

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"

    def test_view_case_action_is_shown_for_chief_views(self):
        """Test view action is shown for chief views."""
        # setup
        self.app.status = ST.PROCESSING
        self.app.case_owner = self.user
        self.app.active_tasks = [Task.TaskType.CHIEF_WAIT]

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"

        self.app.active_tasks = [Task.TaskType.CHIEF_ERROR]
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_shown_when_variation_request_and_not_case_worker(self):
        """An application being processed by another ilb admin (via a variation request)"""
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        self.app.case_owner = User(first_name="Another", last_name="User")
        self.app.active_tasks = []

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_shown_when_app_is_rejected(self):
        """An application rejected by the current case officer"""
        # setup
        self.app.status = ST.COMPLETED
        self.app.case_owner = self.user
        self.app.active_tasks = [Task.TaskType.REJECTED]

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)

        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"

        # Other case owners don't see rejected apps
        self.app.case_owner = User(first_name="Another", last_name="User")
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert not action.show_link()

    def test_view_case_is_shown_when_documents_are_being_signed(self):
        # setup
        self.app.status = ST.PROCESSING
        self.app.case_owner = self.user
        self.app.active_tasks = [Task.TaskType.DOCUMENT_SIGNING]

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"
        assert wb_action.section_label == "Authorise Documents"

    def test_view_case_is_shown_when_documents_signing_has_an_error(self):
        # setup
        self.app.status = ST.PROCESSING
        self.app.case_owner = self.user
        self.app.active_tasks = [Task.TaskType.DOCUMENT_ERROR]

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"
        assert wb_action.section_label == "Authorise Documents"

    def test_view_case_is_shown_when_an_application_has_been_revoked(self):
        # setup
        self.app.status = ST.REVOKED
        self.app.case_owner = self.user
        self.app.active_tasks = [Task.TaskType.CHIEF_REVOKE_WAIT]

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"
        assert wb_action.section_label == "CHIEF Wait for Revocation"

        self.app.active_tasks = [Task.TaskType.CHIEF_ERROR]
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"
        assert wb_action.section_label == "CHIEF Error"

    def test_view_case_action_not_shown(self):
        # setup (App still in progress)
        self.app.status = ST.IN_PROGRESS
        self.app.case_owner = self.user
        self.app.active_tasks = [Task.TaskType.PREPARE]

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ViewApplicationCaseAction.from_config(config)
        assert not action.show_link()

    def test_take_ownership_action_is_shown(self):
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        self.app.case_owner = None
        self.app.active_tasks = []

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = TakeOwnershipAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Take Ownership"
        assert wb_action.section_label == "Application Processing"

        # Test Out for update.
        self.app.active_tasks.append(TT.PREPARE)
        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.section_label == "Application Processing, Out for Update"

        # Test FIR
        self.app.annotation_open_fir_pks = [1]
        self.app.active_tasks.append(TT.PREPARE)
        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.section_label == (
            "Application Processing, Out for Update, Further Information Requested"
        )

        # Test various out for email messages
        self.app.active_tasks = []
        self.app.annotation_open_fir_pks = []
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = TakeOwnershipAction.from_config(config)
        assert action.show_link()

        self.app.open_case_emails = [CaseEmailCodes.BEIS_CASE_EMAIL]
        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Take Ownership"
        assert wb_action.section_label == "Application Processing (Awaiting BEIS Email Response)"

        self.app.open_case_emails = [CaseEmailCodes.CONSTABULARY_CASE_EMAIL]
        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Take Ownership"
        assert (
            wb_action.section_label
            == "Application Processing (Awaiting Constabulary Email Response)"
        )

        self.app.open_case_emails = [CaseEmailCodes.HSE_CASE_EMAIL]
        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Take Ownership"
        assert wb_action.section_label == "Application Processing (Awaiting HSE Email Response)"

        self.app.open_case_emails = [
            CaseEmailCodes.SANCTIONS_CASE_EMAIL,
        ]
        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Take Ownership"
        assert (
            wb_action.section_label == "Application Processing (Awaiting Sanctions Email Response)"
        )

    def test_take_ownership_action_not_shown(self):
        # setup (case owner is not set)
        self.app.status = ST.VARIATION_REQUESTED
        self.app.case_owner = self.user
        self.app.active_tasks = []

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = TakeOwnershipAction.from_config(config)
        assert not action.show_link()

    def test_manage_application_action_is_shown(self):
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        self.app.case_owner = self.user
        self.app.active_tasks = [TT.PROCESS]
        self.app.annotation_open_fir_pks = []

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ManageApplicationAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Manage"
        assert wb_action.section_label == "Application Processing"

        # Test Out for update.
        self.app.active_tasks.append(TT.PREPARE)
        action = ManageApplicationAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Manage"
        assert wb_action.section_label == "Application Processing, Out for Update"

        # Test Further Information Requested
        self.app.annotation_open_fir_pks = [1]
        self.app.active_tasks.append(TT.PREPARE)
        action = ManageApplicationAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Manage"
        assert (
            wb_action.section_label
            == "Application Processing, Out for Update, Further Information Requested"
        )

    def test_manage_application_action_not_shown(self):
        # setup (case owner is not set)
        self.app.status = ST.VARIATION_REQUESTED
        self.app.case_owner = None
        self.app.active_tasks = [TT.PROCESS]

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ManageApplicationAction.from_config(config)
        assert not action.show_link()

    @pytest.mark.parametrize(
        "app_status, active_task, has_withdrawal, is_case_owner, should_show",
        [
            (ST.SUBMITTED, TT.PROCESS, True, True, True),
            (ST.SUBMITTED, TT.PROCESS, True, False, True),  # Not the caseworker
            (ST.SUBMITTED, TT.PROCESS, False, True, False),  # No withdrawal
            (ST.SUBMITTED, TT.PROCESS, False, False, False),  # No withdrawal or caseworker
            #
            (ST.PROCESSING, TT.PROCESS, True, True, True),
            (ST.PROCESSING, TT.PROCESS, True, False, True),  # Not the caseworker
            (ST.PROCESSING, TT.PROCESS, False, True, False),  # No withdrawal
            (ST.PROCESSING, TT.PROCESS, False, False, False),  # No withdrawal or caseworker
            #
            (ST.VARIATION_REQUESTED, TT.PROCESS, True, True, True),
            (ST.VARIATION_REQUESTED, TT.PROCESS, True, False, True),  # Not the caseworker
            (ST.VARIATION_REQUESTED, TT.PROCESS, False, True, False),  # No withdrawal
            (
                ST.VARIATION_REQUESTED,
                TT.PROCESS,
                False,
                False,
                False,
            ),  # No withdrawal or caseworker
        ]
        # Check all other statuses do not show (only the status is invalid in these tests)
        + [
            (status, TT.PROCESS, True, True, False)
            for status in ImpExpStatus
            if status not in [ST.SUBMITTED, ST.PROCESSING, ST.VARIATION_REQUESTED]
        ]
        # Check all other tasks do not show (Only the task is invalid in these tests)
        + [(ST.SUBMITTED, task, True, True, False) for task in TT if task != TT.PROCESS],
    )
    def test_manage_withdrawals_action(
        self, app_status, active_task, has_withdrawal, is_case_owner, should_show
    ):
        # Setup
        self.app.status = app_status
        self.app.active_tasks = [active_task]
        self.app.annotation_has_withdrawal = has_withdrawal

        if is_case_owner:
            self.app.case_owner = self.user

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = ManageWithdrawApplicationAction.from_config(config)

        assert action.show_link() == should_show

        if should_show:
            expected_name = "Withdrawal Request" if is_case_owner else "View Withdrawal Request"

            wb_action = action.get_workbasket_actions()[0]
            assert wb_action.name == expected_name
            assert wb_action.section_label == "Withdraw Pending"

    def test_authorise_documents_action_is_shown(self):
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        self.app.active_tasks = [TT.AUTHORISE]
        self.app.case_owner = self.user

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = AuthoriseDocumentsAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Authorise Documents"

    def test_authorise_documents_action_not_shown(self):
        # setup
        self.app.status = ST.IN_PROGRESS
        self.app.active_tasks = [TT.PREPARE]
        self.app.case_owner = self.user

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = AuthoriseDocumentsAction.from_config(config)
        assert not action.show_link()

    def test_authorise_documents_action_not_shown_different_caseworker(self):
        # setup
        self.app.status = ST.PROCESSING
        self.app.active_tasks = [TT.AUTHORISE]
        self.app.case_owner = User(first_name="Another", last_name="User")

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = AuthoriseDocumentsAction.from_config(config)
        assert not action.show_link()

    def test_cancel_authorisation_action_is_shown(self):
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        self.app.active_tasks = [TT.AUTHORISE]
        self.app.case_owner = self.user

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = CancelAuthorisationAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Cancel Authorisation"

    def test_cancel_authorisation_action_not_shown(self):
        # setup
        self.app.status = ST.IN_PROGRESS
        self.app.active_tasks = [TT.PREPARE]
        self.app.case_owner = self.user

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = CancelAuthorisationAction.from_config(config)
        assert not action.show_link()

    def test_cancel_authorisation_action_not_shown_different_caseworker(self):
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        self.app.active_tasks = [TT.AUTHORISE]
        self.app.case_owner = User(first_name="Another", last_name="User")

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = CancelAuthorisationAction.from_config(config)
        assert not action.show_link()

    @pytest.mark.parametrize("valid_status", (ST.PROCESSING, ST.VARIATION_REQUESTED))
    def test_check_case_document_generation_is_shown(self, valid_status):
        # setup
        self.app.status = valid_status
        self.app.active_tasks = [TT.DOCUMENT_SIGNING]
        self.app.case_owner = self.user

        # tests
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = CheckCaseDocumentGenerationAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Monitor Progress"

    def test_check_case_document_generation_is_not_shown(self):
        # setup
        self.app.status = ST.IN_PROGRESS
        self.app.active_tasks = [TT.PREPARE]
        self.app.case_owner = self.user

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = CheckCaseDocumentGenerationAction.from_config(config)
        assert not action.show_link()

    @pytest.mark.parametrize("valid_status", (ST.PROCESSING, ST.VARIATION_REQUESTED))
    def test_check_case_document_generation_action_not_shown_different_caseworker(
        self, valid_status
    ):
        # setup
        self.app.status = valid_status
        self.app.active_tasks = [TT.DOCUMENT_SIGNING]
        self.app.case_owner = User(first_name="Another", last_name="User")

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = CheckCaseDocumentGenerationAction.from_config(config)
        assert not action.show_link()

    @pytest.mark.parametrize("valid_status", (ST.PROCESSING, ST.VARIATION_REQUESTED))
    def test_recreate_case_documents_is_shown(self, valid_status):
        # setup
        self.app.status = valid_status
        self.app.active_tasks = [TT.DOCUMENT_ERROR]
        self.app.case_owner = self.user

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = RecreateCaseDocumentsAction.from_config(config)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Recreate Case Documents"

    def test_recreate_case_documents_is_not_shown(self):
        # setup
        self.app.status = ST.IN_PROGRESS
        self.app.active_tasks = [TT.PREPARE]
        self.app.case_owner = self.user

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = RecreateCaseDocumentsAction.from_config(config)
        assert not action.show_link()

    @pytest.mark.parametrize("valid_status", (ST.PROCESSING, ST.VARIATION_REQUESTED))
    def test_recreate_case_documents_action_not_shown_different_caseworker(self, valid_status):
        # setup
        self.app.status = valid_status
        self.app.active_tasks = [TT.DOCUMENT_ERROR]
        self.app.case_owner = User(first_name="Another", last_name="User")

        # test
        config = ActionConfig(user=self.user, case_type="import", application=self.app)
        action = RecreateCaseDocumentsAction.from_config(config)
        assert not action.show_link()

    def test_get_workbasket_sections(self, ilb_admin_user, importer):
        user = ilb_admin_user
        case_type = "import"
        application = WoodQuotaApplication(pk=1, status=ST.VARIATION_REQUESTED, importer=importer)
        application.active_tasks = []  # This is to fake the active_tasks annotation
        application.annotation_open_fir_pks = []
        application.open_case_emails = []

        sections = get_workbasket_admin_sections(user, case_type, application)
        names = []
        for section in sections:
            names.extend([a.name for a in section.actions])

        assert sorted(names) == ["Take Ownership", "View"]

        for section in sections:
            for action in section.actions:
                if action.name == "View":
                    assert action.url == f"/case/import/{application.pk}/admin/manage/"
