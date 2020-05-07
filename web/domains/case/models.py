from django.db import models
from web.domains.file.models import File
from web.domains.user.models import User
# from config.settings.base import DATETIME_FORMAT


class VariationRequest(models.Model):
    """Variation requests for licenses or certificates issued requested by
    import/export contacts."""

    OPEN = 'OPEN'
    DRAFT = 'DRAFT'
    CANCELLED = 'CANCELLED'
    REJECTED = 'REJECTED'
    ACCEPTED = 'ACCEPTED'
    WITHDRAWN = 'WITHDRAWN'
    DELETED = 'DELETED'
    CLOSED = 'CLOSED'

    STATUSES = ((DRAFT, 'Draft'), (OPEN, 'Open'), (CANCELLED, 'Cancelled'),
                (REJECTED, 'Rejected'), (ACCEPTED, 'Accepted'),
                (WITHDRAWN, 'Withdrawn'), (DELETED, 'Deleted'), (CLOSED,
                                                                 'Closed'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(max_length=30,
                              choices=STATUSES,
                              blank=False,
                              null=False)
    extension_flag = models.BooleanField(blank=False,
                                         null=False,
                                         default=False)
    requested_datetime = models.DateTimeField(blank=True,
                                              null=True,
                                              auto_now_add=True)
    requested_by = models.ForeignKey(User,
                                     on_delete=models.PROTECT,
                                     blank=True,
                                     null=True,
                                     related_name='requested_variations')
    what_varied = models.CharField(max_length=4000, blank=True, null=True)
    why_varied = models.CharField(max_length=4000, blank=True, null=True)
    when_varied = models.DateField(blank=True, null=True)
    reject_reason = models.CharField(max_length=4000, blank=True, null=True)
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(User,
                                  on_delete=models.PROTECT,
                                  blank=True,
                                  null=True,
                                  related_name='closed_variations')


class UpdateRequest(models.Model):
    """Application update requests for import/export cases requested from
    applicants by case officers"""

    DRAFT = 'DRAFT'
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    UPDATE_IN_PROGRESS = 'UPDATE_IN_PROGRESS'
    RESPONDED = 'RESPONDED'
    DELETED = 'DELETED'

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(max_length=30, blank=False, null=False)
    request_subject = models.CharField(max_length=100, blank=False, null=True)
    request_detail = models.TextField(blank=False, null=True)
    email_cc_address_list = models.CharField(max_length=4000,
                                             blank=True,
                                             null=True)
    response_detail = models.TextField(blank=False, null=True)
    request_datetime = models.DateTimeField(blank=True, null=True)
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='requested_import_application_updates')
    response_datetime = models.DateTimeField(blank=True, null=True)
    response_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='responded_import_application_updates')
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='closed_import_application_updates')


class CaseNote(models.Model):

    DRAFT = 'DRAFT'
    DELETED = 'DELETED'
    COMPLETED = 'COMPLETED'
    STATUSES = ((DRAFT, 'Draft'), (DELETED, 'Deleted'), (COMPLETED,
                                                         'Completed'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    status = models.CharField(max_length=20,
                              choices=STATUSES,
                              blank=False,
                              null=False,
                              default=DRAFT)
    note = models.TextField(blank=True, null=True)
    create_datetime = models.DateTimeField(blank=False,
                                           null=False,
                                           auto_now_add=True)
    created_by = models.ForeignKey(User,
                                   on_delete=models.PROTECT,
                                   blank=False,
                                   null=False,
                                   related_name='created_import_case_notes')
    files = models.ManyToManyField(File)
