from typing import Any, ClassVar

from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.views import View
from django.views.generic.detail import SingleObjectMixin

from web.domains.case.services import case_progress
from web.domains.case.shared import ImpExpStatus
from web.domains.case.types import ImpOrExp
from web.domains.case.utils import end_process_task
from web.models import Process, Task
from web.types import AuthenticatedHttpRequest


class ApplicationTaskMixin(SingleObjectMixin, View):
    """Mixin to define the expected application status & task type.

    Overrides get and post methods to ensure the following attributes are set:
        * self.application
        * self.task
    """

    # Application record
    application: ImpOrExp

    # Current active task
    task: Task | None

    # Used to fetch the object.
    model = Process
    pk_url_kwarg = "application_pk"

    # The expected current status of the process record
    current_status: ClassVar[list[ImpExpStatus]]

    # The expected current active task of the process record
    current_task_type: ClassVar[Task.TaskType | None] = None

    # The next status to set.
    next_status: ClassVar[str | None] = None

    # The next task type to set
    next_task_type: ClassVar[str | None] = None

    http_method_names = ["get", "post"]

    def __init__(self, *args, **kwargs):
        self.task = None
        self.application = None  # type:ignore[assignment]
        self.object = None

        super().__init__(*args, **kwargs)

    def setup(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> Any:
        for attr in ["current_status"]:
            if not hasattr(self, attr):
                raise ImproperlyConfigured(f"The following class attribute must be set: {attr!r}")

        return super().setup(request, *args, **kwargs)

    def set_application_and_task(self) -> None:
        self.application = self.get_object()
        self.task = self.get_task()

        if not self.has_object_permission():
            raise PermissionDenied

    def has_object_permission(self) -> bool:
        """Implement in child view if required."""
        return True

    def get_object(self, queryset: models.QuerySet | None = None) -> ImpOrExp:
        """Downcast to specific model class."""

        application = super().get_object(queryset).get_specific_model()
        case_progress.check_expected_status(application, self.current_status)
        self.object = application

        return application

    def get_task(self) -> Task | None:
        """Load the expected current task"""
        task = None
        is_post = self.request.method == "POST"

        if self.current_task_type:
            task = case_progress.get_expected_task(
                self.application, self.current_task_type, select_for_update=is_post
            )

        return task

    def get_queryset(self) -> "models.QuerySet[ImpOrExp]":
        """Return the model instance ready for update."""

        if self.request.method == "POST":
            return self.model.objects.select_for_update().all()

        return self.model.objects.all()

    def update_application_status(self, commit: bool = True) -> None:
        """Set the application status to the next status."""

        if self.next_status:
            self.application.status = self.next_status

        if commit:
            self.application.save()

    def update_application_tasks(self) -> None:
        """Update the application task set to the next task."""

        if self.current_task_type and self.task:
            end_process_task(self.task, self.request.user)

        if self.next_task_type:
            Task.objects.create(
                process=self.application, task_type=self.next_task_type, previous=self.task
            )

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.set_application_and_task()

        return super().get(request, *args, **kwargs)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.set_application_and_task()

        return super().post(request, *args, **kwargs)


class ApplicationAndTaskRelatedObjectMixin:
    """Useful when updating objects relating to an application.

    e.g. A variation request associated with an application.
    The task and status checks still need performing for the application.
    """

    application: ImpOrExp
    task: Task | None = None

    # The expected current status of the process record
    current_status: ClassVar[list[ImpExpStatus]]

    # The expected current active task of the process record
    current_task_type: ClassVar[Task.TaskType | None] = None

    # The next status to set.
    next_status: ClassVar[str | None] = None

    # The next task type to set
    next_task_type: ClassVar[str | None] = None

    def get_application(self) -> ImpOrExp:
        application = Process.objects.get(
            pk=self.kwargs["application_pk"]  # type: ignore[attr-defined]
        ).get_specific_model()

        case_progress.check_expected_status(application, self.current_status)

        return application

    def set_application_and_task(self) -> None:
        self.application = self.get_application()

        if self.current_task_type:
            self.task = case_progress.get_expected_task(
                self.application,
                self.current_task_type,
                select_for_update=self.request.method == "POST",  # type: ignore[attr-defined]
            )

        if not self.has_object_permission():
            raise PermissionDenied

    def has_object_permission(self) -> bool:
        """Implement in child view if required."""
        return True

    def get(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> Any:
        self.set_application_and_task()
        return super().get(request, *args, **kwargs)  # type: ignore[misc]

    def post(self, request: AuthenticatedHttpRequest, *args: Any, **kwargs: Any) -> Any:
        self.set_application_and_task()
        return super().post(request, *args, **kwargs)  # type: ignore[misc]

    def update_application_status(self, commit: bool = True) -> None:
        """Set the application status to the next status."""

        if self.next_status:
            self.application.status = self.next_status

        if commit:
            self.application.save()

    def update_application_tasks(self) -> None:
        """Update the application task set to the next task."""

        if self.current_task_type and self.task:
            end_process_task(self.task, self.request.user)  # type: ignore[attr-defined]

        if self.next_task_type:
            Task.objects.create(
                process=self.application, task_type=self.next_task_type, previous=self.task
            )
