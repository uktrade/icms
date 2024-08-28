import uuid
from random import randint

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q, QuerySet

from web.flow.models import Process
from web.mail.constants import CaseEmailCodes
from web.types import TypedTextChoices

from .shared import ImpExpStatus


class VariationRequest(models.Model):
    """Variation requests for licenses or certificates issued requested by
    import/export contacts."""

    class Statuses(TypedTextChoices):
        DRAFT = ("DRAFT", "Draft")
        OPEN = ("OPEN", "Open")
        CANCELLED = ("CANCELLED", "Cancelled")
        REJECTED = ("REJECTED", "Rejected")
        ACCEPTED = ("ACCEPTED", "Accepted")
        WITHDRAWN = ("WITHDRAWN", "Withdrawn")
        DELETED = ("DELETED", "Deleted")
        CLOSED = ("CLOSED", "Closed")

    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=30, choices=Statuses.choices)
    extension_flag = models.BooleanField(default=False)
    requested_datetime = models.DateTimeField(auto_now_add=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_variations"
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
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="closed_variations",
    )


class UpdateRequest(models.Model):
    """Update requests are sent by case officers and allow editing the case again."""

    class Status(TypedTextChoices):
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
        verbose_name="Response to Request",
        null=True,
        help_text="Please either confirm acceptance of the updates requested or your reason for no updates being made",
    )
    request_datetime = models.DateTimeField(null=True)

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )

    response_datetime = models.DateTimeField(blank=True, null=True)

    response_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )

    closed_datetime = models.DateTimeField(blank=True, null=True)

    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
    )


class CaseNoteStatuses(models.Manager):
    def active(self):
        return self.filter(is_active=True)

    def inactive(self):
        return self.filter(is_active=False)


class CaseNote(models.Model):
    objects = CaseNoteStatuses()

    note = models.TextField(blank=True, null=True)
    files = models.ManyToManyField("web.File")
    is_active = models.BooleanField(blank=False, null=False, default=True)

    create_datetime = models.DateTimeField(blank=False, null=False, auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_import_case_notes",
    )

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="+"
    )

    class Meta:
        ordering = ["-create_datetime"]


class WithdrawApplication(models.Model):
    class Statuses(TypedTextChoices):
        OPEN = ("OPEN", "Open")
        REJECTED = ("REJECTED", "Rejected")
        ACCEPTED = ("ACCEPTED", "Accepeted")
        DELETED = ("DELETED", "Deleted")

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
    status = models.CharField(max_length=10, choices=Statuses.choices, default=Statuses.OPEN)
    reason = models.TextField()
    request_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )

    response = models.TextField()
    response_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True, related_name="+"
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
    """

    class Meta:
        abstract = True

    DEFAULT_REF = "Not Assigned"

    # Decision
    REFUSE = "REFUSE"
    APPROVE = "APPROVE"
    DECISIONS = ((APPROVE, "Approve Application"), (REFUSE, "Refuse Application"))

    # Note: There are too many places to refactor this in this pr.
    # At some point it would be better if everything called ImpExpStatus directly.
    Statuses = ImpExpStatus

    status = models.CharField(
        max_length=30,
        choices=Statuses.choices,
        default=Statuses.IN_PROGRESS,
    )

    # The date and time the application was first submitted
    submit_datetime = models.DateTimeField(blank=True, null=True)

    # The date and time the application was last submitted
    last_submit_datetime = models.DateTimeField(blank=True, null=True)

    # Used exclusively in search to indicate when a case has been reassigned.
    reassign_datetime = models.DateTimeField(blank=True, null=True)

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

    def get_reference(self) -> str:
        return self.reference or self.DEFAULT_REF

    def current_update_requests(self) -> QuerySet[UpdateRequest]:
        st = UpdateRequest.Status

        update_requests = self.update_requests.filter(
            is_active=True, status__in=[st.OPEN, st.UPDATE_IN_PROGRESS, st.RESPONDED]
        )

        return update_requests


class CaseEmail(models.Model):
    class Status(TypedTextChoices):
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

    template_code = models.CharField(max_length=30, choices=CaseEmailCodes.choices)
    subject = models.CharField(max_length=100, null=True)
    body = models.TextField(max_length=4000, null=True)
    attachments = models.ManyToManyField("web.File")

    response = models.TextField(max_length=4000, null=True)

    sent_datetime = models.DateTimeField(null=True)

    # Optional because not all V1 emails have this data.
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )

    closed_datetime = models.DateTimeField(null=True)

    # Optional because not all V1 emails have this data.
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="+",
    )

    @property
    def is_draft(self):
        return self.status == self.Status.DRAFT


def create_check_code() -> int:
    return randint(10000000, 99999999)


class DownloadLinkBase(models.Model):
    """Base model used to send links in emails to download documents."""

    class Meta:
        abstract = True

    FAILURE_LIMIT = 3

    # Used in email link to load record.
    code = models.UUIDField(default=uuid.uuid4, editable=False)

    # Found in email to prove the user has access to the mailbox
    check_code = models.CharField(max_length=8, editable=False, default=create_check_code)
    email = models.EmailField(max_length=254)
    failure_count = models.IntegerField(default=0)
    expired = models.BooleanField(default=False)
    sent_at_datetime = models.DateTimeField(auto_now_add=True)


class CaseEmailDownloadLink(DownloadLinkBase):
    """Model used to send links in case emails to download attached documents."""

    case_email = models.ForeignKey("web.CaseEmail", on_delete=models.PROTECT)


class DocumentPackBase(models.Model):
    """Base class for Import Licences and Export Certificates"""

    class Meta:
        abstract = True

    class Status(TypedTextChoices):
        DRAFT = "DR"
        ACTIVE = "AC"
        ARCHIVED = "AR"
        REVOKED = "RE"

    status = models.TextField(choices=Status.choices, max_length=2, default=Status.DRAFT)

    # This is set when the licence / certificate is set to active.
    case_reference = models.CharField(
        max_length=100, null=True, unique=True, verbose_name="Case Reference"
    )

    # Set when a licence is revoked
    revoke_reason = models.TextField(null=True)
    revoke_email_sent = models.BooleanField(default=False)

    # Values added when records are created / updated, used to get the most recent one.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CaseDocumentReference(models.Model):
    """All documents relevant to a case licence or certificate."""

    class Type(TypedTextChoices):
        LICENCE = ("LICENCE", "Licence")
        CERTIFICATE = ("CERTIFICATE", "Certificate")
        COVER_LETTER = ("COVER_LETTER", "Cover Letter")

    document = models.OneToOneField("web.File", on_delete=models.CASCADE, null=True)
    document_type = models.CharField(max_length=12, choices=Type.choices)

    # Nullable because import application cover letters don't have a reference.
    reference = models.CharField(max_length=20, verbose_name="Document Reference", null=True)

    # Code to verify document at /check
    check_code = models.CharField(null=True, max_length=16, default=create_check_code)

    # Fields to set up the generic model for import / export models.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        o_id, dt, ref = (self.object_id, self.document_type, self.reference)
        return f"CaseDocumentReference(object_id={o_id}, document_type={dt}, reference={ref})"
