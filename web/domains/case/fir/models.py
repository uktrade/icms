from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from viewflow.models import Process

from web.domains.file.models import File
from web.domains.user.models import User


class FurtherInformationRequest(models.Model):
    """
    Further information requests for cases requested from
    applicant by case officers
    """

    DRAFT = "DRAFT"
    CLOSED = "CLOSED"
    DELETED = "DELETED"
    OPEN = "OPEN"
    RESPONDED = "RESPONDED"

    STATUSES = (
        (DRAFT, "Draft"),
        (CLOSED, "CLOSED"),
        (DELETED, "Deleted"),
        (OPEN, "Open"),
        (RESPONDED, "Responded"),
    )

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(
        max_length=20, choices=STATUSES, blank=False, null=False, default=DRAFT
    )
    request_subject = models.CharField(max_length=100, blank=False, null=True)
    request_detail = models.TextField(blank=False, null=True)
    email_cc_address_list = models.CharField(max_length=4000, blank=True, null=True)
    requested_datetime = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    response_detail = models.CharField(max_length=4000, blank=False, null=True)
    response_datetime = models.DateTimeField(blank=True, null=True)
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="requested_further_import_information",
    )
    response_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="responded_import_information_requests",
    )
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="closed_import_information_requests",
    )
    deleted_datetime = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="deleted_import_information_requests",
    )
    files = models.ManyToManyField(File, blank=True)

    def is_draft(self):
        return self.status == self.DRAFT

    def delete(self):
        self.status = self.DELETED
        self.is_active = False
        self.save()

    def close(self, user):
        self.status = self.CLOSED
        self.closed_datetime = timezone.now()
        self.closed_by = user
        self.save()

    def date_created_formatted(self):
        """
            returns a formatted datetime
        """
        return self.requested_datetime.strftime("%d-%b-%Y %H:%M:%S")


class FurtherInformationRequestProcess(Process):
    """
        Further information request process
    """

    fir = models.ForeignKey(FurtherInformationRequest, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    parent_process = GenericForeignKey("content_type", "object_id")

    def send_request_task(self):
        """
            Return send_request task of fir process for editing draft FIRs.
        """

        # Lazy import to prevent circular dependency
        from .flows import FurtherInformationRequestFlow

        task = (
            self.active_tasks().filter(flow_task=FurtherInformationRequestFlow.send_request).last()
        )
        return task

    def review_task(self):
        """
            Return review task of fir process for closing FIRs.
        """
        # Lazy import to prevent circular dependency
        from .flows import FurtherInformationRequestFlow

        task = self.active_tasks().filter(flow_task=FurtherInformationRequestFlow.review).last()
        return task

    @property
    def parent_display(self):
        """
            Text representation of parent process. Used in FIR emails.
        """
        return self.parent_process
