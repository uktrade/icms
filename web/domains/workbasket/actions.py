from typing import TYPE_CHECKING, Any, Type

from django.urls import reverse

from web.domains.case.shared import ImpExpStatus
from web.flow.models import Task

from .base import WorkbasketAction

if TYPE_CHECKING:
    from web.domains.case.types import ImpOrExp
    from web.domains.user.models import User


class Action:
    """Base class for all actions.

    Determines if an action should be shown in the workbasket.
    """

    def __init__(
        self, user: "User", case_type: str, application: "ImpOrExp", tasks: list[str]
    ) -> None:
        self.user = user
        self.case_type = case_type
        self.application = application
        self.active_tasks = tasks
        self.status = self.application.status

    def show_link(self) -> bool:
        raise NotImplementedError

    def get_workbasket_action(self) -> WorkbasketAction:
        raise NotImplementedError

    def is_case_owner(self) -> bool:
        return self.application.case_owner == self.user

    def get_kwargs(self) -> dict[str, Any]:
        return {"application_pk": self.application.pk, "case_type": self.case_type}


class TakeOwnershipAction(Action):
    def show_link(self) -> bool:
        show_link = False

        if self.status == ImpExpStatus.VARIATION_REQUESTED:
            if not self.application.case_owner:
                show_link = True

        return show_link

    def get_workbasket_action(self) -> WorkbasketAction:
        kwargs = self.get_kwargs()

        return WorkbasketAction(
            is_post=True,
            name="Take Ownership",
            url=reverse("case:take-ownership", kwargs=kwargs),
        )


class ManageApplicationAction(Action):
    def show_link(self) -> bool:
        show_link = False

        if self.status == ImpExpStatus.VARIATION_REQUESTED:
            if self.is_case_owner() and Task.TaskType.PROCESS in self.active_tasks:
                show_link = True

        return show_link

    def get_workbasket_action(self) -> WorkbasketAction:
        kwargs = self.get_kwargs()

        return WorkbasketAction(
            is_post=False, name="Manage", url=reverse("case:manage", kwargs=kwargs)
        )


class AuthoriseDocumentsAction(Action):
    def show_link(self) -> bool:
        show_link = False

        if self.status == ImpExpStatus.VARIATION_REQUESTED:
            if Task.TaskType.AUTHORISE in self.active_tasks:
                show_link = True

        return show_link

    def get_workbasket_action(self) -> WorkbasketAction:
        kwargs = self.get_kwargs()

        return WorkbasketAction(
            is_post=False,
            name="Authorise Documents",
            url=reverse("case:authorise-documents", kwargs=kwargs),
        )


class CancelAuthorisationAction(Action):
    def show_link(self) -> bool:
        show_link = False

        if self.status == ImpExpStatus.VARIATION_REQUESTED:
            if Task.TaskType.AUTHORISE in self.active_tasks:
                show_link = True

        return show_link

    def get_workbasket_action(self) -> WorkbasketAction:
        kwargs = self.get_kwargs()

        return WorkbasketAction(
            is_post=True,
            name="Cancel Authorisation",
            url=reverse("case:cancel-authorisation", kwargs=kwargs),
        )


class SubmitVariationUpdateAction(Action):
    def show_link(self) -> bool:
        show_link = False

        if self.status == ImpExpStatus.VARIATION_REQUESTED:
            if Task.TaskType.VR_REQUEST_CHANGE in self.active_tasks:
                show_link = True

        return show_link

    def get_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_kwargs()

        # Didn't use VariationRequest.OPEN to lazily avoid circular dependency
        return kwargs | {
            "variation_request_pk": self.application.variation_requests.get(status="OPEN").pk
        }

    def get_workbasket_action(self) -> WorkbasketAction:
        kwargs = self.get_kwargs()

        # TODO: ICMSLST-1304 Add Submit Update view
        return WorkbasketAction(
            is_post=False,
            name="Submit Update",
            url=reverse("case:variation-request-submit-update", kwargs=kwargs),
        )


class ViewApplicationAction(Action):
    def show_link(self) -> bool:
        return True

    def get_workbasket_action(self) -> WorkbasketAction:
        kwargs = self.get_kwargs()

        return WorkbasketAction(is_post=False, name="View", url=reverse("case:view", kwargs=kwargs))


ActionT = Type[Action]

# If everything was replaced this would just be a list of actions
REQUEST_VARIATION_ADMIN_ACTIONS: list[ActionT] = [
    # Management views
    TakeOwnershipAction,
    ManageApplicationAction,
    # Post management (authorise view)
    AuthoriseDocumentsAction,
    CancelAuthorisationAction,
    # Misc views
    ViewApplicationAction,
]

# Applicant workbasket actions
REQUEST_VARIATION_APPLICANT_ACTIONS: list[ActionT] = [SubmitVariationUpdateAction]


def get_workbasket_actions(
    user: "User", case_type: str, application: "ImpOrExp"
) -> list[WorkbasketAction]:
    """Returns all admin actions that should be shown for this application.

    Note: This is only called when the application status is VARIATION_REQUESTED.
    It could however be used to fetch all workbasket actions, assuming all the logic is
    moved here.
    """

    return _get_workbasket_actions(user, case_type, application, REQUEST_VARIATION_ADMIN_ACTIONS)


def get_workbasket_applicant_actions(
    user: "User", case_type: str, application: "ImpOrExp"
) -> list[WorkbasketAction]:
    """Returns all applicant actions that should be shown for this application.

    Note: This is only called when the application status is VARIATION_REQUESTED.
    It could however be used to fetch all workbasket actions, assuming all the logic is
    moved here.
    """

    return _get_workbasket_actions(
        user, case_type, application, REQUEST_VARIATION_APPLICANT_ACTIONS
    )


def _get_workbasket_actions(
    user: "User", case_type: str, application: "ImpOrExp", workbasket_actions: list[ActionT]
):
    if application.status != ImpExpStatus.VARIATION_REQUESTED:
        raise ValueError("Not all actions have been migrated.")

    tasks = application.get_active_task_list()
    actions = []

    for action_cls in workbasket_actions:
        action = action_cls(
            user=user,
            case_type=case_type,
            application=application,
            tasks=tasks,
        )

        if action.show_link():
            actions.append(action.get_workbasket_action())

    return actions
