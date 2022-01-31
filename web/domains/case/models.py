from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import messages
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from web.domains.file.models import File
from web.domains.user.models import User
from web.domains.workbasket.actions import (
    get_workbasket_admin_sections,
    get_workbasket_applicant_sections,
)
from web.domains.workbasket.base import WorkbasketBase, WorkbasketRow
from web.flow.models import Process, Task
from web.types import AuthenticatedHttpRequest

from .shared import ImpExpStatus

CASE_NOTE_DRAFT = "DRAFT"
CASE_NOTE_COMPLETED = "COMPLETED"
CASE_NOTE_STATUSES = (
    (CASE_NOTE_DRAFT, "Draft"),
    (CASE_NOTE_COMPLETED, "Completed"),
)

if TYPE_CHECKING:
    from django.db.models import QuerySet


class VariationRequest(models.Model):
    """Variation requests for licenses or certificates issued requested by
    import/export contacts."""

    OPEN = "OPEN"
    DRAFT = "DRAFT"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    ACCEPTED = "ACCEPTED"
    WITHDRAWN = "WITHDRAWN"
    DELETED = "DELETED"
    CLOSED = "CLOSED"

    STATUSES = (
        (DRAFT, "Draft"),
        (OPEN, "Open"),
        (CANCELLED, "Cancelled"),
        (REJECTED, "Rejected"),
        (ACCEPTED, "Accepted"),
        (WITHDRAWN, "Withdrawn"),
        (DELETED, "Deleted"),
        (CLOSED, "Closed"),
    )

    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=30, choices=STATUSES)
    extension_flag = models.BooleanField(default=False)
    requested_datetime = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="requested_variations"
    )
    what_varied = models.CharField(
        max_length=4000, verbose_name="What would you like to vary about the current licence(s)"
    )

    why_varied = models.CharField(
        max_length=4000,
        verbose_name="Why would you like to vary the licence(s) in this way",
        null=True,
    )

    when_varied = models.DateField(
        verbose_name="What date would the varied licence(s) come into effect", null=True
    )

    reject_cancellation_reason = models.CharField(
        max_length=4000, null=True, verbose_name="Cancellation reason"
    )

    update_request_reason = models.CharField(
        max_length=4000, null=True, verbose_name="Description of the changes required"
    )

    closed_datetime = models.DateTimeField(null=True)
    closed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, related_name="closed_variations"
    )


class UpdateRequest(models.Model):
    """Update requests are sent by case officers and allow editing the case again."""

    class Status(models.TextChoices):
        DRAFT: str = ("DRAFT", "Draft")  # type:ignore[assignment]
        OPEN: str = ("OPEN", "Open")  # type:ignore[assignment]
        CLOSED: str = ("CLOSED", "Closed")  # type:ignore[assignment]
        UPDATE_IN_PROGRESS: str = (
            "UPDATE_IN_PROGRESS",
            "Update in Progress",
        )  # type:ignore[assignment]
        RESPONDED: str = ("RESPONDED", "Responded")  # type:ignore[assignment]
        DELETED: str = ("DELETED", "Deleted")  # type:ignore[assignment]

    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=30, choices=Status.choices)

    request_subject = models.CharField(max_length=100, null=True)
    request_detail = models.TextField(null=True)
    response_detail = models.TextField(
        verbose_name="Summary of Changes",
        null=True,
        help_text="Please enter a summary of the updates made",
    )
    request_datetime = models.DateTimeField(null=True)

    requested_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )

    response_datetime = models.DateTimeField(blank=True, null=True)

    response_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )

    closed_datetime = models.DateTimeField(blank=True, null=True)

    closed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )


class CaseNoteStatuses(models.Manager):
    def draft(self):
        return self.filter(is_active=True, status=CASE_NOTE_DRAFT)

    def completed(self):
        return self.filter(is_active=True, status=CASE_NOTE_COMPLETED)

    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class CaseNote(models.Model):
    objects = CaseNoteStatuses()

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(
        max_length=20, choices=CASE_NOTE_STATUSES, blank=False, null=False, default=CASE_NOTE_DRAFT
    )
    note = models.TextField(blank=True, null=True)
    create_datetime = models.DateTimeField(blank=False, null=False, auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="created_import_case_notes",
    )
    files = models.ManyToManyField(File)

    class Meta:
        ordering = ["-create_datetime"]


class WithdrawApplication(models.Model):
    STATUS_OPEN = "open"
    STATUS_REJECTED = "rejected"
    STATUS_ACCEPTED = "accepted"

    OPEN = (STATUS_OPEN, "OPEN")
    REJECTED = (STATUS_REJECTED, "REJECTED")
    ACCEPTED = (STATUS_ACCEPTED, "ACCEPTED")
    STATUSES = (OPEN, REJECTED, ACCEPTED)

    # alternative to having two foreignkeys here would be to have
    # ManyToMany(WithdrawApplication, ...) on both Import/ExportApplication, but
    # that is not really better:
    #
    #  -it would allow for weird bugs where a single WithdrawApplication is
    #  linked to multiple import/exportapplications
    #
    # see constraints below, the DB will enforce that exactly one of these is
    # always set

    import_application = models.ForeignKey(
        "ImportApplication", on_delete=models.PROTECT, related_name="withdrawals", null=True
    )

    export_application = models.ForeignKey(
        "ExportApplication", on_delete=models.PROTECT, related_name="withdrawals", null=True
    )

    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=10, choices=STATUSES, default=STATUS_OPEN)
    reason = models.TextField()
    request_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="+")

    response = models.TextField()
    response_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )

    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(import_application__isnull=False) | Q(export_application__isnull=False),
                name="application_one_null",
            ),
            models.CheckConstraint(
                check=Q(import_application__isnull=True) | Q(export_application__isnull=True),
                name="application_one_not_null",
            ),
        ]


class ApplicationBase(WorkbasketBase, Process):
    """Common base class for Import/ExportApplication. Needed because some
    common code needs a Django model class to work with (see
    ResponsePreparationForm).

    TODO: possibly move more duplicated stuff from Import/ExportApplication to here.
    """

    class Meta:
        abstract = True

    DEFAULT_REF = "Not Assigned"

    # Decision
    REFUSE = "REFUSE"
    APPROVE = "APPROVE"
    DECISIONS = ((APPROVE, "Approve"), (REFUSE, "Refuse"))

    # Note: There are too many places to refactor this in this pr.
    # At some point it would be better if everything called ImpExpStatus directly.
    Statuses = ImpExpStatus

    status = models.CharField(
        max_length=30,
        choices=Statuses.choices,
        default=Statuses.IN_PROGRESS,
    )

    submit_datetime = models.DateTimeField(blank=True, null=True)

    # This is the "Case Reference" field
    reference = models.CharField(max_length=100, blank=True, null=True, unique=True)

    decision = models.CharField(max_length=10, choices=DECISIONS, blank=True, null=True)
    refuse_reason = models.CharField(
        max_length=4000, blank=True, null=True, verbose_name="Refusal reason"
    )

    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )

    acknowledged_datetime = models.DateTimeField(null=True)

    def is_import_application(self) -> bool:
        raise NotImplementedError

    def get_edit_view_name(self) -> str:
        """Get the edit view name."""
        raise NotImplementedError

    def user_is_contact_of_org(self, user: User) -> bool:
        """Is the user a contact of the org (Importer or Exporter)"""
        raise NotImplementedError

    def user_is_agent_of_org(self, user: User) -> bool:
        """Is the user agent of the org (Importer or Exporter)"""
        raise NotImplementedError

    def get_org_contacts(self) -> "QuerySet[User]":
        """Org (Importer or Exporter) contacts."""
        raise NotImplementedError

    def get_agent_contacts(self) -> "QuerySet[User]":
        """Agent contacts."""
        raise NotImplementedError

    def get_workbasket_subject(self) -> str:
        """Get workbasket subject/topic column content."""
        raise NotImplementedError

    def get_reference(self) -> str:
        return self.reference or self.DEFAULT_REF

    def get_workbasket_row(self, user: User) -> WorkbasketRow:
        """Get data to show in the workbasket."""

        r = WorkbasketRow()

        r.reference = self.get_reference()

        r.subject = self.get_workbasket_subject()

        r.timestamp = self.created

        r.status = self.get_status_display()

        if self.is_import_application():
            r.company = self.importer  # type: ignore[attr-defined]
            case_type = "import"
        else:
            r.company = self.exporter  # type: ignore[attr-defined]
            case_type = "export"

        r.company_agent = self.agent  # type: ignore[attr-defined]

        is_ilb_admin = user.has_perm("web.ilb_admin")
        include_applicant_rows = not is_ilb_admin or settings.DEBUG_SHOW_ALL_WORKBASKET_ROWS

        if is_ilb_admin:
            admin_sections = get_workbasket_admin_sections(
                user=user, case_type=case_type, application=self
            )

            for section in admin_sections:
                r.sections.append(section)

        if include_applicant_rows:
            applicant_sections = get_workbasket_applicant_sections(
                user=user, case_type=case_type, application=self
            )

            for section in applicant_sections:
                r.sections.append(section)

        return r

    def submit_application(self, request: AuthenticatedHttpRequest, task: Task) -> None:
        # this needs to be here to avoid circular dependencies
        from web.domains.case.utils import allocate_case_reference

        if self.is_import_application():
            prefix = "IMA"
        else:
            # TODO: Export application (Good Manufacturing Practice) apparently
            # uses a "GA" prefix for some reason. put that in when/if we
            # implement GMP application type.
            prefix = "CA"

        if not self.reference:
            self.reference = allocate_case_reference(
                lock_manager=request.icms.lock_manager, prefix=prefix, use_year=True, min_digits=5
            )

        # if case owner is present, an update request has just been filed
        if self.case_owner:
            # Only change to processing if it's not a variation request
            if self.status != self.Statuses.VARIATION_REQUESTED:
                self.status = self.Statuses.PROCESSING
        else:
            self.status = self.Statuses.SUBMITTED

        self.submit_datetime = timezone.now()
        self.submitted_by = request.user
        self.save()

        task.is_active = False
        task.finished = timezone.now()
        task.save()

        Task.objects.create(process=self, task_type=Task.TaskType.PROCESS, previous=task)

    def redirect_after_submit(self, request: AuthenticatedHttpRequest) -> HttpResponse:
        msg = (
            f"Your application has been submitted. The reference number"
            f" assigned to this case is {self.get_reference()}."
        )
        messages.success(request, msg)

        return redirect(reverse("workbasket"))

    def current_update_requests(self):
        st = UpdateRequest.Status

        update_requests = self.update_requests.filter(
            is_active=True, status__in=[st.OPEN, st.UPDATE_IN_PROGRESS, st.RESPONDED]
        )

        return update_requests

    def history(self) -> None:
        """Debug method to print the history of the application"""

        print("*-" * 40)
        print(f"Current status: {self.get_status_display()}")

        all_tasks = self.tasks.all().order_by("created")
        active = all_tasks.filter(is_active=True)

        print("Active Tasks in order:")
        for t in active:
            print(f"Task: {t.get_task_type_display()}, {t.created}, {t.finished}")

        print("All tasks in order:")
        for t in all_tasks:
            created = t.created.strftime("%Y/%m/%d %H:%M")
            finished = t.finished.strftime("%Y/%m/%d %H:%M") if t.finished else ""
            print(f"Task: {t.get_task_type_display()}, created={created!r}, finished={finished!r}")

        print("*-" * 40)

    def get_information(self, is_ilb_admin: bool):
        """Return the latest information about an application.

        TODO: This needs a lot of work to flesh out what it is supposed to show.
        :param is_ilb_admin: This will probably be needed to determine what the user should see here...
        """

        if self.is_rejected():
            return "View Case"

        return "Application Processing"

    def is_rejected(self, active_tasks: list[str] = None):
        """Is the application in a rejected state."""

        if not active_tasks:
            active_tasks = self.get_active_task_list()

        return self.status == self.Statuses.COMPLETED and Task.TaskType.REJECTED in active_tasks


class CaseEmail(models.Model):
    class Status(models.TextChoices):
        OPEN = ("OPEN", "Open")
        CLOSED = ("CLOSED", "Closed")
        DRAFT = ("DRAFT", "Draft")

    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=30, default=Status.DRAFT)

    to = models.EmailField(max_length=254, null=True)

    cc_address_list = ArrayField(
        models.EmailField(max_length=254),
        help_text="Enter CC email addresses separated by a comma",
        verbose_name="Cc",
        size=15,
        blank=True,
        null=True,
    )

    subject = models.CharField(max_length=100, null=True)
    body = models.TextField(max_length=4000, null=True)
    attachments = models.ManyToManyField(File)

    response = models.TextField(max_length=4000, null=True)

    sent_datetime = models.DateTimeField(null=True)
    closed_datetime = models.DateTimeField(null=True)

    @property
    def is_draft(self):
        return self.status == self.Status.DRAFT
