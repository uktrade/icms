import pytest
from django.test import override_settings

from web.domains.case._import.wood.models import WoodQuotaApplication
from web.domains.case.shared import ImpExpStatus
from web.domains.user.models import User
from web.domains.workbasket.actions import get_workbasket_actions
from web.domains.workbasket.actions.ilb_admin_actions import (
    AuthoriseDocumentsAction,
    CancelAuthorisationAction,
    ManageApplicationAction,
    TakeOwnershipAction,
    ViewApplicationCaseAction,
)
from web.domains.workbasket.actions.shared_actions import ClearApplicationAction
from web.flow.models import Task


class TestAdminActions:
    user: User
    app: WoodQuotaApplication
    TT = Task.TaskType
    ST = ImpExpStatus

    @pytest.fixture(autouse=True)
    def setup(self, test_icms_admin_user):
        self.user = test_icms_admin_user
        # set pk as it's the minimum needed to craft the url
        self.app = WoodQuotaApplication(pk=1)

    def test_view_case_action_is_shown(self):
        """A freshly submitted application (no case_owner yet)"""
        # setup
        self.app.status = self.ST.SUBMITTED
        self.app.case_owner = None
        active_tasks = []

        # test
        action = ViewApplicationCaseAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_is_shown_app_processing_another_admin(self):
        """An application being processed by another ilb admin"""
        # setup
        self.app.status = self.ST.PROCESSING
        self.app.case_owner = User(first_name="Another", last_name="User")
        active_tasks = []

        # test
        action = ViewApplicationCaseAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_is_shown_when_authorised(self):
        # setup
        self.app.status = self.ST.PROCESSING
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.AUTHORISE]

        # test
        action = ViewApplicationCaseAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    @override_settings(ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD=True)
    def test_view_case_action_is_shown_for_chief_views(self):
        """Test view action is shown for chief views."""
        # setup
        self.app.status = self.ST.PROCESSING
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.CHIEF_WAIT]

        # test
        action = ViewApplicationCaseAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

        active_tasks = [Task.TaskType.CHIEF_ERROR]
        action = ViewApplicationCaseAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_shown_when_variation_request_and_not_case_worker(self):
        """An application being processed by another ilb admin (via a variation request)"""
        # setup
        self.app.status = self.ST.VARIATION_REQUESTED
        self.app.case_owner = User(first_name="Another", last_name="User")
        active_tasks = []

        # test
        action = ViewApplicationCaseAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View"

    def test_view_case_action_shown_when_app_is_rejected(self):
        """An application rejected by the current case officer"""
        # setup
        self.app.status = self.ST.COMPLETED
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.REJECTED]

        # test
        action = ViewApplicationCaseAction(self.user, "import", self.app, active_tasks, True, True)

        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "View Case"

        # Other case owners don't see rejected apps
        self.app.case_owner = User(first_name="Another", last_name="User")
        action = ViewApplicationCaseAction(self.user, "import", self.app, active_tasks, True, True)
        assert not action.show_link()

    def test_view_case_action_not_shown(self):
        # setup (App still in progress)
        self.app.status = self.ST.IN_PROGRESS
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.PREPARE]

        # test
        action = ViewApplicationCaseAction(self.user, "import", self.app, active_tasks, True, True)
        assert not action.show_link()

    def test_authorise_documents_action_is_shown(self):
        # setup
        self.app.status = self.ST.VARIATION_REQUESTED
        active_tasks = [self.TT.AUTHORISE]

        # test
        action = AuthoriseDocumentsAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Authorise Documents"

    def test_authorise_documents_action_not_shown(self):
        # setup
        self.app.status = self.ST.IN_PROGRESS
        active_tasks = [self.TT.PREPARE]
        # test
        action = AuthoriseDocumentsAction(self.user, "import", self.app, active_tasks, True, True)
        assert not action.show_link()

    def test_cancel_authorisation_action_is_shown(self):
        # setup
        self.app.status = self.ST.VARIATION_REQUESTED
        active_tasks = [self.TT.AUTHORISE]

        # test
        action = CancelAuthorisationAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Cancel Authorisation"

    def test_cancel_authorisation_action_not_shown(self):
        # setup
        self.app.status = self.ST.IN_PROGRESS
        active_tasks = [self.TT.PREPARE]

        # test
        action = CancelAuthorisationAction(self.user, "import", self.app, active_tasks, True, True)
        assert not action.show_link()

    def test_manage_application_action_is_shown(self):
        # setup
        self.app.status = self.ST.VARIATION_REQUESTED
        self.app.case_owner = self.user
        active_tasks = [self.TT.PROCESS]

        # test
        action = ManageApplicationAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Manage"

    def test_manage_application_action_not_shown(self):
        # setup (case owner is not set)
        self.app.status = self.ST.VARIATION_REQUESTED
        self.app.case_owner = None
        active_tasks = [self.TT.PROCESS]

        # test
        action = ManageApplicationAction(self.user, "import", self.app, active_tasks, True, True)
        assert not action.show_link()

    def test_take_ownership_action_is_shown(self):
        # setup
        self.app.status = self.ST.VARIATION_REQUESTED
        self.app.case_owner = None
        active_tasks = []

        # test
        action = TakeOwnershipAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Take Ownership"

    def test_take_ownership_action_not_shown(self):
        # setup (case owner is not set)
        self.app.status = self.ST.VARIATION_REQUESTED
        self.app.case_owner = self.user
        active_tasks = []

        # test
        action = TakeOwnershipAction(self.user, "import", self.app, active_tasks, True, True)
        assert not action.show_link()

    def test_clear_application_action_is_shown(self):
        """Admins only see the clear link if its rejected and they are the case owner."""
        # setup
        self.app.status = self.ST.COMPLETED
        self.app.case_owner = self.user
        active_tasks = [Task.TaskType.REJECTED]

        # test
        action = ClearApplicationAction(self.user, "import", self.app, active_tasks, True, True)
        assert action.show_link()

        wb_action = action.get_workbasket_actions()[0]
        assert wb_action.name == "Clear"

    def test_clear_application_action_not_shown(self):
        """An app rejected by another case owner should not be shown"""
        # setup
        self.app.status = self.ST.COMPLETED
        self.app.case_owner = User(first_name="Another", last_name="User")
        active_tasks = [Task.TaskType.REJECTED]

        # test
        action = ClearApplicationAction(self.user, "import", self.app, active_tasks, True, True)
        assert not action.show_link()

    def test_get_workbasket_actions(self, test_icms_admin_user):
        user = test_icms_admin_user
        case_type = "import"
        application = WoodQuotaApplication(
            pk=1,
            status=self.ST.VARIATION_REQUESTED,
        )

        actions = get_workbasket_actions(user, case_type, application)

        names = [a.name for a in actions]

        assert sorted(names) == ["Take Ownership", "View"]

        # Check the view endpoint is the management link
        view_action = next(a for a in actions if a.name == "View")
        assert view_action.url == f"/case/import/{application.pk}/admin/manage/"
