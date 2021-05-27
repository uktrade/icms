from django.db import models

from web.domains.file.models import File
from web.domains.user.models import User
from web.domains.workbasket.base import WorkbasketBase
from web.flow.models import Process


class FIRStatuses(models.Manager):
    def completed(self):
        return self.filter(status__in=[self.model.CLOSED, self.model.RESPONDED])

    def active(self):
        return self.filter(is_active=True)

    def draft(self):
        return self.filter(status=self.model.DRAFT)

    def open(self):
        return self.filter(status=self.model.OPEN)

    def closed(self):
        return self.filter(status=self.model.CLOSED)

    def responded(self):
        return self.filter(status=self.model.RESPONDED)

    def submitted(self):
        return self.filter(status__in=[self.model.OPEN, self.model.RESPONDED, self.model.CLOSED])


# TODO: ICMSLST-703 adapt to new workbasket -->
class FurtherInformationRequest(WorkbasketBase, Process):
    """Further information requests for cases requested from
    applicant by case officers"""

    PROCESS_TYPE = "FurtherInformationRequest"

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

    objects = FIRStatuses()

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

    class Meta:
        ordering = ["-requested_datetime"]
