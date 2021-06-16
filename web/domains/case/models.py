from django.db import models
from django.db.models import Q
from django.urls import reverse

from web.domains.file.models import File
from web.domains.user.models import User
from web.domains.workbasket.base import WorkbasketAction, WorkbasketBase, WorkbasketRow
from web.flow.models import Process

CASE_NOTE_DRAFT = "DRAFT"
CASE_NOTE_COMPLETED = "COMPLETED"
CASE_NOTE_STATUSES = (
    (CASE_NOTE_DRAFT, "Draft"),
    (CASE_NOTE_COMPLETED, "Completed"),
)


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
    """Application update requests for import/export cases requested from
    applicants by case officers"""

    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    UPDATE_IN_PROGRESS = "UPDATE_IN_PROGRESS"
    RESPONDED = "RESPONDED"
    DELETED = "DELETED"

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(max_length=30, blank=False, null=False)
    request_subject = models.CharField(max_length=100, blank=False, null=True)
    request_detail = models.TextField(blank=False, null=True)
    email_cc_address_list = models.CharField(max_length=4000, blank=True, null=True)
    response_detail = models.TextField(blank=False, null=True)
    request_datetime = models.DateTimeField(blank=True, null=True)
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="requested_import_application_updates",
    )
    response_datetime = models.DateTimeField(blank=True, null=True)
    response_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="responded_import_application_updates",
    )
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="closed_import_application_updates",
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

    decision = models.CharField(max_length=10, choices=DECISIONS, blank=True, null=True)
    refuse_reason = models.CharField(max_length=4000, blank=True, null=True)

    def is_import_application(self) -> bool:
        raise NotImplementedError

    def get_edit_view_name(self) -> str:
        """Get the edit view name."""
        raise NotImplementedError

    def get_workbasket_subject(self) -> str:
        """Get workbasket subject/topic column content."""
        raise NotImplementedError

    def get_workbasket_row(self, user: User) -> WorkbasketRow:
        """Get data to show in the workbasket."""

        r = WorkbasketRow()

        # TODO: use self.reference once that's properly filled in
        r.reference = self.pk

        r.subject = self.get_workbasket_subject()

        r.timestamp = self.created

        r.status = self.get_status_display()

        # TODO: this was harcoded in the template, no idea what this should be
        r.information = "Application Processing"

        if self.is_import_application():
            r.company = self.importer
            case_type = "import"
        else:
            r.company = self.exporter
            case_type = "export"

        # common kwargs
        kwargs = {"application_pk": self.pk, "case_type": case_type}

        view_action = WorkbasketAction(
            is_post=False, name="View", url=reverse("case:view", kwargs=kwargs)
        )

        task = self.get_active_task()

        if user.has_perm("web.reference_data_access"):
            admin_actions: list[WorkbasketAction] = []

            if self.status in [self.SUBMITTED, self.WITHDRAWN]:
                if not self.case_owner:
                    admin_actions.append(
                        WorkbasketAction(
                            is_post=True,
                            name="Take Ownership",
                            url=reverse("case:take-ownership", kwargs=kwargs),
                        ),
                    )

                    admin_actions.append(view_action)

                elif (self.case_owner == user) and task and task.task_type == "process":
                    admin_actions.append(
                        WorkbasketAction(
                            is_post=False, name="Manage", url=reverse("case:manage", kwargs=kwargs)
                        )
                    )
                else:
                    admin_actions.append(view_action)

            elif self.status == self.PROCESSING:
                # TODO: implement this
                admin_actions.append(
                    WorkbasketAction(is_post=False, name="Authorise Documents", url="#TODO")
                )

                admin_actions.append(
                    WorkbasketAction(
                        is_post=True,
                        name="Cancel Authorisation",
                        url=reverse("case:cancel-authorisation", kwargs=kwargs),
                    )
                )

                admin_actions.append(view_action)

            if admin_actions:
                r.actions.append(admin_actions)

        # TODO: we shouldn't always show the applicant actions, but we need to be able to test the system.
        if True:
            applicant_actions: list[WorkbasketAction] = []

            if self.status == self.SUBMITTED:
                applicant_actions.append(view_action)

                applicant_actions.append(
                    WorkbasketAction(
                        is_post=False,
                        name="Withdraw",
                        url=reverse("case:withdraw-case", kwargs=kwargs),
                    ),
                )

                for fir in self.further_information_requests.open():
                    applicant_actions.append(
                        WorkbasketAction(
                            is_post=False,
                            name="Respond FIR",
                            url=reverse("case:respond-fir", kwargs=kwargs | {"fir_pk": fir.pk}),
                        )
                    )

            elif self.status == self.WITHDRAWN:
                applicant_actions.append(view_action)

                applicant_actions.append(
                    WorkbasketAction(
                        is_post=False,
                        name="Pending Withdrawal",
                        url=reverse("case:withdraw-case", kwargs=kwargs),
                    ),
                )

            elif self.status == self.IN_PROGRESS:
                applicant_actions.append(
                    WorkbasketAction(
                        is_post=False,
                        name="Resume",
                        url=reverse(self.get_edit_view_name(), kwargs={"application_pk": self.pk}),
                    )
                )

            if applicant_actions:
                r.actions.append(applicant_actions)

        return r
