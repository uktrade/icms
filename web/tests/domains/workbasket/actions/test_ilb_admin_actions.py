import pytest

from web.domains.case.shared import ImpExpStatus
from web.domains.workbasket.actions import get_workbasket_admin_sections
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
from web.domains.workbasket.actions.shared_actions import ClearApplicationAction
from web.models import Task, User, WoodQuotaApplication

ST = ImpExpStatus
TT = Task.TaskType


class TestAdminActions:
    user: User
    app: WoodQuotaApplication

    @pytest.fixture(autouse=True)
    def setup(self, test_icms_admin_user):
        self.user = test_icms_admin_user
        # set pk as it's the minimum needed to craft the url
        self.app = WoodQuotaApplication(pk=1)

    def test_view_case_action_is_shown(self):
        """A freshly submitted application (no case_owner yet)"""
        # setup
        self.app.status = ST.SUBMITTED
        self.app.case_owner = None
        active_tasks = []

        # test
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_is_shown_app_processing_another_admin(self):
        """An application being processed by another ilb admin"""
        # setup
        self.app.status = ST.PROCESSING
        self.app.case_owner = User(first_name="Another", last_name="User")
        active_tasks = []

        # test
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_is_shown_when_authorised(self):
        # setup
        self.app.status = ST.PROCESSING
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.AUTHORISE]

        # test
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"

    def test_view_case_action_is_shown_for_chief_views(self):
        """Test view action is shown for chief views."""
        # setup
        self.app.status = ST.PROCESSING
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.CHIEF_WAIT]

        # test
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

        active_tasks = [Task.TaskType.CHIEF_ERROR]
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_shown_when_variation_request_and_not_case_worker(self):
        """An application being processed by another ilb admin (via a variation request)"""
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        self.app.case_owner = User(first_name="Another", last_name="User")
        active_tasks = []

        # test
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_shown_when_app_is_rejected(self):
        """An application rejected by the current case officer"""
        # setup
        self.app.status = ST.COMPLETED
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.REJECTED]

        # test
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, True
        )

        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"

        # Other case owners don't see rejected apps
        self.app.case_owner = User(first_name="Another", last_name="User")
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, True
        )
        assert not action.show_link()

    def test_view_case_is_shown_when_documents_are_being_signed(self):
        # setup
        self.app.status = ST.PROCESSING
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.DOCUMENT_SIGNING]

        # test
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"
        assert wb_action.section_label == "Authorise Documents"

    def test_view_case_is_shown_when_documents_signing_has_an_error(self):
        # setup
        self.app.status = ST.PROCESSING
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.DOCUMENT_ERROR]

        # test
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"
        assert wb_action.section_label == "Authorise Documents"

    def test_view_case_is_shown_when_an_application_has_been_revoked(self):
        # setup
        self.app.status = ST.REVOKED
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.CHIEF_REVOKE_WAIT]

        # test
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"
        assert wb_action.section_label == "CHIEF Wait for Revocation"

        active_tasks = [Task.TaskType.CHIEF_ERROR]
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"
        assert wb_action.section_label == "CHIEF Error"

    def test_view_case_action_not_shown(self):
        # setup (App still in progress)
        self.app.status = ST.IN_PROGRESS
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.PREPARE]

        # test
        action = ViewApplicationCaseAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert not action.show_link()

    def test_take_ownership_action_is_shown(self):
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        self.app.case_owner = None
        active_tasks = []

        # test
        action = TakeOwnershipAction(self.user, "import", self.app, active_tasks, True, True, False)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Take Ownership"

    def test_take_ownership_action_not_shown(self):
        # setup (case owner is not set)
        self.app.status = ST.VARIATION_REQUESTED
        self.app.case_owner = self.user
        active_tasks = []

        # test
        action = TakeOwnershipAction(self.user, "import", self.app, active_tasks, True, True, False)
        assert not action.show_link()

    def test_manage_application_action_is_shown(self):
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        self.app.case_owner = self.user
        active_tasks = [TT.PROCESS]

        # test
        action = ManageApplicationAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Manage"

    def test_manage_application_action_not_shown(self):
        # setup (case owner is not set)
        self.app.status = ST.VARIATION_REQUESTED
        self.app.case_owner = None
        active_tasks = [TT.PROCESS]

        # test
        action = ManageApplicationAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert not action.show_link()

    def test_clear_application_action_is_shown(self):
        """Admins only see the clear link if its rejected and they are the case owner."""
        # setup
        self.app.status = ST.COMPLETED
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.REJECTED]

        # test
        action = ClearApplicationAction(
            self.user, "import", self.app, active_tasks, True, True, True
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Clear"

    def test_clear_application_action_not_shown(self):
        """An app rejected by another case owner should not be shown"""
        # setup
        self.app.status = ST.COMPLETED
        self.app.case_owner = User(first_name="Another", last_name="User")
        active_tasks = [Task.TaskType.REJECTED]

        # test
        action = ClearApplicationAction(
            self.user, "import", self.app, active_tasks, True, True, True
        )
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
        active_tasks = [active_task]
        self.app.annotation_has_withdrawal = has_withdrawal

        if is_case_owner:
            self.app.case_owner = self.user

        # test
        action = ManageWithdrawApplicationAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )

        assert action.show_link() == should_show

        if should_show:
            expected_name = "Withdrawal Request" if is_case_owner else "View Withdrawal Request"

            wb_action = action.get_workbasket_actions()[0]
            assert wb_action.name == expected_name
            assert wb_action.section_label == "Withdraw Pending"

    def test_authorise_documents_action_is_shown(self):
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        active_tasks = [TT.AUTHORISE]
        self.app.case_owner = self.user

        # test
        action = AuthoriseDocumentsAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Authorise Documents"

    def test_authorise_documents_action_not_shown(self):
        # setup
        self.app.status = ST.IN_PROGRESS
        active_tasks = [TT.PREPARE]
        self.app.case_owner = self.user

        # test
        action = AuthoriseDocumentsAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert not action.show_link()

    def test_authorise_documents_action_not_shown_different_caseworker(self):
        # setup
        self.app.status = ST.PROCESSING
        active_tasks = [TT.AUTHORISE]
        self.app.case_owner = User(first_name="Another", last_name="User")

        # test
        action = AuthoriseDocumentsAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert not action.show_link()

    def test_cancel_authorisation_action_is_shown(self):
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        active_tasks = [TT.AUTHORISE]
        self.app.case_owner = self.user

        # test
        action = CancelAuthorisationAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Cancel Authorisation"

    def test_cancel_authorisation_action_not_shown(self):
        # setup
        self.app.status = ST.IN_PROGRESS
        active_tasks = [TT.PREPARE]
        self.app.case_owner = self.user

        # test
        action = CancelAuthorisationAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert not action.show_link()

    def test_cancel_authorisation_action_not_shown_different_caseworker(self):
        # setup
        self.app.status = ST.VARIATION_REQUESTED
        active_tasks = [TT.AUTHORISE]
        self.app.case_owner = User(first_name="Another", last_name="User")

        # test
        action = CancelAuthorisationAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert not action.show_link()

    @pytest.mark.parametrize("valid_status", (ST.PROCESSING, ST.VARIATION_REQUESTED))
    def test_check_case_document_generation_is_shown(self, valid_status):
        # setup
        self.app.status = valid_status
        active_tasks = [TT.DOCUMENT_SIGNING]
        self.app.case_owner = self.user

        # tests
        action = CheckCaseDocumentGenerationAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Monitor Progress"

    def test_check_case_document_generation_is_not_shown(self):
        # setup
        self.app.status = ST.IN_PROGRESS
        active_tasks = [TT.PREPARE]
        self.app.case_owner = self.user

        # test
        action = CheckCaseDocumentGenerationAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert not action.show_link()

    @pytest.mark.parametrize("valid_status", (ST.PROCESSING, ST.VARIATION_REQUESTED))
    def test_check_case_document_generation_action_not_shown_different_caseworker(
        self, valid_status
    ):
        # setup
        self.app.status = valid_status
        active_tasks = [TT.DOCUMENT_SIGNING]
        self.app.case_owner = User(first_name="Another", last_name="User")

        # test
        action = CheckCaseDocumentGenerationAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert not action.show_link()

    @pytest.mark.parametrize("valid_status", (ST.PROCESSING, ST.VARIATION_REQUESTED))
    def test_recreate_case_documents_is_shown(self, valid_status):
        # setup
        self.app.status = valid_status
        active_tasks = [TT.DOCUMENT_ERROR]
        self.app.case_owner = self.user

        # test
        action = RecreateCaseDocumentsAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Recreate Case Documents"

    def test_recreate_case_documents_is_not_shown(self):
        # setup
        self.app.status = ST.IN_PROGRESS
        active_tasks = [TT.PREPARE]
        self.app.case_owner = self.user

        # test
        action = RecreateCaseDocumentsAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert not action.show_link()

    @pytest.mark.parametrize("valid_status", (ST.PROCESSING, ST.VARIATION_REQUESTED))
    def test_recreate_case_documents_action_not_shown_different_caseworker(self, valid_status):
        # setup
        self.app.status = valid_status
        active_tasks = [TT.DOCUMENT_ERROR]
        self.app.case_owner = User(first_name="Another", last_name="User")

        # test
        action = RecreateCaseDocumentsAction(
            self.user, "import", self.app, active_tasks, True, True, False
        )
        assert not action.show_link()

    def test_get_workbasket_sections(self, test_icms_admin_user):
        user = test_icms_admin_user
        case_type = "import"
        application = WoodQuotaApplication(
            pk=1,
            status=ST.VARIATION_REQUESTED,
        )
        application.active_tasks = []  # This is to fake the active_tasks annotation

        sections = get_workbasket_admin_sections(user, case_type, application)
        names = []
        for section in sections:
            names.extend([a.name for a in section.actions])

        assert sorted(names) == ["Take Ownership", "View"]

        for section in sections:
            for action in section.actions:
                if action.name == "View":
                    assert action.url == f"/case/import/{application.pk}/admin/manage/"
