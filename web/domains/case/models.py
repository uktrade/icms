from typing import TYPE_CHECKING, Any, Optional

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
from web.domains.workbasket.base import WorkbasketAction, WorkbasketBase, WorkbasketRow
from web.flow.models import Process, Task
from web.types import AuthenticatedHttpRequest

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

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(max_length=30, choices=STATUSES, blank=False, null=False)
    extension_flag = models.BooleanField(blank=False, null=False, default=False)
    requested_datetime = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    requested_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="requested_variations"
    )
    what_varied = models.CharField(max_length=4000, blank=True, null=True)
    why_varied = models.CharField(max_length=4000, blank=True, null=True)
    when_varied = models.DateField(blank=True, null=True)
    reject_reason = models.CharField(max_length=4000, blank=True, null=True)
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="closed_variations"
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

    email_cc_address_list = ArrayField(
        models.EmailField(max_length=254),
        help_text=(
            "You may enter a list of email addresses to CC this email to. Use a comma (,) to"
            " seperate multiple addresses. E.g. john@smith.com,jane@smith.com"
        ),
        verbose_name="Request CC Email Addresses",
        size=15,
        blank=True,
        null=True,
    )

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

    # Decision
    REFUSE = "REFUSE"
    APPROVE = "APPROVE"
    DECISIONS = ((APPROVE, "Approve"), (REFUSE, "Refuse"))

    # TODO: ICMSLST-634 see if we can remove the type:ignores once we have django-stubs
    class Statuses(models.TextChoices):
        IN_PROGRESS: str = ("IN_PROGRESS", "In Progress")  # type:ignore[assignment]
        SUBMITTED: str = ("SUBMITTED", "Submitted")  # type:ignore[assignment]
        PROCESSING: str = ("PROCESSING", "Processing")  # type:ignore[assignment]
        CHIEF: str = ("CHIEF", "CHIEF")  # type:ignore[assignment]
        COMPLETED: str = ("COMPLETED", "Completed")  # type:ignore[assignment]
        WITHDRAWN: str = ("WITHDRAWN", "Withdrawn")  # type:ignore[assignment]
        STOPPED: str = ("STOPPED", "Stopped")  # type:ignore[assignment]
        VARIATION_REQUESTED: str = (
            "VARIATION_REQUESTED",
            "Variation Requested",
        )  # type:ignore[assignment]
        REVOKED: str = ("REVOKED", "Revoked")  # type:ignore[assignment]
        DELETED: str = ("DELETED", "Deleted")  # type:ignore[assignment]
        UPDATE_REQUESTED: str = ("UPDATE_REQUESTED", "Update Requested")  # type:ignore[assignment]

    status = models.CharField(
        max_length=30,
        choices=Statuses.choices,
        default=Statuses.IN_PROGRESS,
    )

    submit_datetime = models.DateTimeField(blank=True, null=True)

    reference = models.CharField(max_length=100, blank=True, null=True, unique=True)

    decision = models.CharField(max_length=10, choices=DECISIONS, blank=True, null=True)
    refuse_reason = models.CharField(max_length=4000, blank=True, null=True)

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
        return self.reference or "Not Assigned"

    def get_workbasket_row(self, user: User) -> WorkbasketRow:
        """Get data to show in the workbasket."""

        r = WorkbasketRow()

        r.reference = self.get_reference()

        r.subject = self.get_workbasket_subject()

        r.timestamp = self.created

        r.status = self.get_status_display()

        # TODO: this was harcoded in the template, no idea what this should be
        r.information = "Application Processing"

        if self.is_import_application():
            r.company = self.importer  # type: ignore[attr-defined]
            case_type = "import"
        else:
            r.company = self.exporter  # type: ignore[attr-defined]
            case_type = "export"

        r.company_agent = self.agent  # type: ignore[attr-defined]

        # common kwargs
        kwargs = {"application_pk": self.pk, "case_type": case_type}

        view_action = WorkbasketAction(
            is_post=False, name="View", url=reverse("case:view", kwargs=kwargs)
        )

        task = self.get_active_task()

        is_ilb_admin = user.has_perm("web.reference_data_access")
        include_applicant_rows = not is_ilb_admin or settings.DEBUG_SHOW_ALL_WORKBASKET_ROWS

        if is_ilb_admin:
            admin_actions = self._get_admin_actions(user, view_action, task, kwargs)

            if admin_actions:
                r.actions.append(admin_actions)

        if include_applicant_rows:
            applicant_actions = self._get_applicant_actions(view_action, kwargs)

            if applicant_actions:
                r.actions.append(applicant_actions)

        return r

    def _get_admin_actions(
        self,
        user: User,
        view_action: WorkbasketAction,
        task: Optional[Task],
        kwargs: dict[str, Any],
    ) -> list[WorkbasketAction]:
        admin_actions: list[WorkbasketAction] = []

        bypass_chief = (
            settings.ALLOW_BYPASS_CHIEF_NEVER_ENABLE_IN_PROD and self.status == self.Statuses.CHIEF
        )

        if self.status in [self.Statuses.SUBMITTED, self.Statuses.WITHDRAWN]:
            case_owner = self.case_owner  # type: ignore[attr-defined]

            if not case_owner:
                admin_actions.append(
                    WorkbasketAction(
                        is_post=True,
                        name="Take Ownership",
                        url=reverse("case:take-ownership", kwargs=kwargs),
                    ),
                )

                admin_actions.append(view_action)

            elif (case_owner == user) and task and task.task_type == Task.TaskType.PROCESS:
                admin_actions.append(
                    WorkbasketAction(
                        is_post=False, name="Manage", url=reverse("case:manage", kwargs=kwargs)
                    )
                )
            else:
                admin_actions.append(view_action)

        elif self.status == self.Statuses.PROCESSING:
            admin_actions.append(
                WorkbasketAction(
                    is_post=False,
                    name="Authorise Documents",
                    url=reverse("case:authorise-documents", kwargs=kwargs),
                )
            )

            admin_actions.append(
                WorkbasketAction(
                    is_post=True,
                    name="Cancel Authorisation",
                    url=reverse("case:cancel-authorisation", kwargs=kwargs),
                )
            )

            admin_actions.append(view_action)

        elif bypass_chief:
            if task and task.task_type == Task.TaskType.CHIEF_WAIT:
                admin_actions.append(
                    WorkbasketAction(
                        is_post=True,
                        name="(TEST) Bypass CHIEF",
                        url=reverse(
                            "import:bypass-chief",
                            kwargs={"application_pk": self.pk, "chief_status": "success"},
                        ),
                    )
                )

                admin_actions.append(
                    WorkbasketAction(
                        is_post=True,
                        name="(TEST) Bypass CHIEF induce failure",
                        url=reverse(
                            "import:bypass-chief",
                            kwargs={"application_pk": self.pk, "chief_status": "failure"},
                        ),
                    )
                )

                admin_actions.append(
                    WorkbasketAction(
                        is_post=True,
                        name="Monitor Progress",
                        url="#TODO: ICMSLST-812 - Popup showing progress",
                    )
                )

            elif task and task.task_type == Task.TaskType.CHIEF_ERROR:
                admin_actions.append(
                    WorkbasketAction(
                        is_post=False,
                        name="Show Licence Details",
                        url="#TODO: ICMSLST-812 - CHIEF Dashboard",
                    )
                )

        elif self.status == self.Statuses.COMPLETED:
            admin_actions.append(view_action)

        return admin_actions

    def _get_applicant_actions(
        self, view_action: WorkbasketAction, kwargs: dict[str, Any]
    ) -> list[WorkbasketAction]:
        applicant_actions: list[WorkbasketAction] = []

        if self.status == self.Statuses.SUBMITTED:
            applicant_actions.append(view_action)

            applicant_actions.append(
                WorkbasketAction(
                    is_post=False,
                    name="Withdraw",
                    url=reverse("case:withdraw-case", kwargs=kwargs),
                ),
            )

            for fir in self.further_information_requests.open():  # type: ignore[attr-defined]
                applicant_actions.append(
                    WorkbasketAction(
                        is_post=False,
                        name="Respond FIR",
                        url=reverse("case:respond-fir", kwargs=kwargs | {"fir_pk": fir.pk}),
                    )
                )

        elif self.status == self.Statuses.WITHDRAWN:
            applicant_actions.append(view_action)

            applicant_actions.append(
                WorkbasketAction(
                    is_post=False,
                    name="Pending Withdrawal",
                    url=reverse("case:withdraw-case", kwargs=kwargs),
                ),
            )

        elif self.status == self.Statuses.IN_PROGRESS:
            applicant_actions.append(
                WorkbasketAction(
                    is_post=False,
                    name="Resume",
                    url=reverse(self.get_edit_view_name(), kwargs={"application_pk": self.pk}),
                )
            )

            applicant_actions.append(
                WorkbasketAction(
                    is_post=True,
                    name="Cancel",
                    url=reverse("case:cancel", kwargs=kwargs),
                    confirm="Are you sure you want to cancel this draft application? All entered data will be lost.",
                )
            )

        elif self.status == self.Statuses.UPDATE_REQUESTED:
            applicant_actions.append(view_action)

            # TODO ICMSLST-958 allow to withdraw when update request is pending
            # applicant_actions.append(
            #    WorkbasketAction(
            #        is_post=False,
            #        name="Withdraw",
            #        url=reverse("case:withdraw-case", kwargs=kwargs),
            #    ),
            # )

            update_requests = self.update_requests.filter(is_active=True).filter(
                status__in=[
                    UpdateRequest.Status.OPEN,
                    UpdateRequest.Status.UPDATE_IN_PROGRESS,
                    UpdateRequest.Status.RESPONDED,
                ]
            )
            for update in update_requests:
                if update.status == UpdateRequest.Status.OPEN:
                    applicant_actions.append(
                        WorkbasketAction(
                            is_post=False,
                            name="Respond to Update Request",
                            url=reverse(
                                "case:start-update-request",
                                kwargs=kwargs | {"update_request_pk": update.pk},
                            ),
                        )
                    )
                elif update.status in [
                    UpdateRequest.Status.UPDATE_IN_PROGRESS,
                    UpdateRequest.Status.RESPONDED,
                ]:
                    applicant_actions.append(
                        WorkbasketAction(
                            is_post=False,
                            name="Resume Update Request",
                            url=reverse(
                                "case:respond-update-request",
                                kwargs=kwargs,
                            ),
                        )
                    )

        elif self.status == self.Statuses.COMPLETED:
            applicant_actions.append(view_action)

            if self.acknowledged_by and self.acknowledged_datetime:
                action = "View Notification"
            else:
                action = "Acknowledge Notification"

            applicant_actions.append(
                WorkbasketAction(
                    is_post=False,
                    name=action,
                    url=reverse("case:ack-notification", kwargs=kwargs),
                ),
            )

        return applicant_actions

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

        self.status = self.Statuses.SUBMITTED
        self.submit_datetime = timezone.now()
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
