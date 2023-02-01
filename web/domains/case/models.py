from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q

from web.domains.file.models import File
from web.domains.user.models import User
from web.flow.models import Process

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


class ApplicationBase(Process):
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
    reference = models.CharField(
        max_length=100, blank=True, null=True, unique=True, verbose_name="Case Reference"
    )

    decision = models.CharField(max_length=10, choices=DECISIONS, blank=True, null=True)
    refuse_reason = models.CharField(
        max_length=4000, blank=True, null=True, verbose_name="Refusal reason"
    )

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

    def get_reference(self) -> str:
        return self.reference or self.DEFAULT_REF

    def current_update_requests(self):
        st = UpdateRequest.Status

        update_requests = self.update_requests.filter(
            is_active=True, status__in=[st.OPEN, st.UPDATE_IN_PROGRESS, st.RESPONDED]
        )

        return update_requests


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


class DocumentPackBase(models.Model):
    """Base class for Import Licences and Export Certificates"""

    class Meta:
        abstract = True

    class Status(models.TextChoices):
        DRAFT = "DR"
        ACTIVE = "AC"
        ARCHIVED = "AR"

    status = models.TextField(choices=Status.choices, max_length=2, default=Status.DRAFT)

    document_references = GenericRelation("CaseDocumentReference")

    # This is set when the licence / certificate is set to active.
    case_reference = models.CharField(
        max_length=100, null=True, unique=True, verbose_name="Case Reference"
    )

    # Values added when records are created / updated, used to get the most recent one.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Used to remove from workbasket when Clear action is performed.
    show_in_workbasket = models.BooleanField(default=True)


class CaseDocumentReference(models.Model):
    """All documents relevant to a case licence or certificate."""

    class Type(models.TextChoices):
        LICENCE = ("LICENCE", "Licence")
        CERTIFICATE = ("CERTIFICATE", "Certificate")
        COVER_LETTER = ("COVER_LETTER", "Cover Letter")

    document = models.OneToOneField(File, on_delete=models.CASCADE, null=True)
    document_type = models.CharField(max_length=12, choices=Type.choices)

    # Nullable because import application cover letters don't have a reference.
    reference = models.CharField(max_length=20, verbose_name="Document Reference", null=True)

    # Fields to set up the generic model for import / export models.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        o_id, dt, ref = (self.object_id, self.document_type, self.reference)
        return f"CaseDocumentReference(object_id={o_id}, document_type={dt}, reference={ref})"
