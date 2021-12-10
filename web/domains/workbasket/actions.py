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


class ViewApplicationAction(Action):
    def show_link(self) -> bool:
        return True

    def get_workbasket_action(self) -> WorkbasketAction:
        kwargs = self.get_kwargs()

        return WorkbasketAction(is_post=False, name="View", url=reverse("case:view", kwargs=kwargs))


# If everything was replaced this would just be a list of actions
REQUEST_VARIATION_ACTIONS: list[Type[Action]] = [
    # Management views
    TakeOwnershipAction,
    ManageApplicationAction,
    # Post management (authorise view)
    AuthoriseDocumentsAction,
    CancelAuthorisationAction,
    # Misc views
    ViewApplicationAction,
]


def get_workbasket_actions(
    user: "User", case_type: str, application: "ImpOrExp"
) -> list[WorkbasketAction]:
    """Returns all actions that should be shown for this application.

    Note: This is only called when the application status is VARIATION_REQUESTED.
    It could however be used to fetch all workbasket actions, assuming all the logic is
    moved here.
    """

    if application.status != ImpExpStatus.VARIATION_REQUESTED:
        raise ValueError("Not all actions have been migrated.")

    tasks: list[str] = list(application.get_active_tasks(False).values_list("task_type", flat=True))

    actions = []

    for action_cls in REQUEST_VARIATION_ACTIONS:
        action = action_cls(
            user=user,
            case_type=case_type,
            application=application,
            tasks=tasks,
        )

        if action.show_link():
            actions.append(action.get_workbasket_action())

    return actions
