from django.db import models

from web.domains.case.fir.models import FurtherInformationRequest
from web.domains.case.models import CaseNote, UpdateRequest, VariationRequest
from web.domains.user.models import User


class ImportCase(models.Model):
    IN_PROGRESS = 'IN_PROGRESS'
    SUBMITTED = 'SUBMITTED'
    PROCESSING = 'PROCESSING'
    COMPLETED = 'COMPLETED'
    WITHDRAWN = 'WITHDRAWN'
    STOPPED = 'STOPPED'
    VARIATION_REQUESTED = 'VARIATION_REQUESTED'
    REVOKED = 'REVOKED'
    DELETED = 'DELETED'

    STATUSES = ((IN_PROGRESS, 'In Progress'), (SUBMITTED, 'Submitted'),
                (PROCESSING, 'Processing'), (COMPLETED, 'Completed'),
                (WITHDRAWN, 'Withdrawn'), (STOPPED, 'Stopped'),
                (REVOKED, 'Revoked'), (VARIATION_REQUESTED,
                                       'Variation Requested'), (DELETED,
                                                                'Deleted'))

    # Chief usage status
    CANCELLED = 'C'
    EXHAUSTED = 'E'
    EXPIRED = 'D'
    SURRENDERED = 'S'
    CHIEF_STATUSES = ((CANCELLED, 'Cancelled'), (EXHAUSTED, 'Exhausted'),
                      (EXPIRED, 'Expired'), (SURRENDERED, 'S'))

    # Decision
    REFUSE = 'REFUSE'
    APPROVE = 'APPROVE'
    DECISIONS = ((REFUSE, 'Refuse'), (APPROVE, 'Approve'))

    status = models.CharField(max_length=30,
                              choices=STATUSES,
                              blank=False,
                              null=False)
    reference = models.CharField(max_length=50, blank=True, null=True)
    variation_no = models.IntegerField(blank=False, null=False, default=0)
    legacy_case_flag = models.BooleanField(blank=False,
                                           null=False,
                                           default=False)
    chief_usage_status = models.CharField(max_length=1,
                                          choices=CHIEF_STATUSES,
                                          blank=True,
                                          null=True)
    under_appeal_flag = models.BooleanField(blank=False,
                                            null=False,
                                            default=False)
    decision = models.CharField(max_length=10,
                                choices=DECISIONS,
                                blank=True,
                                null=True)
    variation_decision = models.CharField(max_length=10,
                                          choices=DECISIONS,
                                          blank=True,
                                          null=True)
    refuse_reason = models.CharField(max_length=4000, blank=True, null=True)
    variation_refuse_reason = models.CharField(max_length=4000,
                                               blank=True,
                                               null=True)
    issue_date = models.DateField(blank=True, null=True)
    licence_start_date = models.DateField(blank=True, null=True)
    licence_end_date = models.DateField(blank=True, null=True)
    licence_extended_flag = models.BooleanField(blank=False,
                                                null=False,
                                                default=False)
    last_update_datetime = models.DateTimeField(blank=False,
                                                null=False,
                                                auto_now=True)
    last_updated_by = models.ForeignKey(User,
                                        on_delete=models.PROTECT,
                                        blank=False,
                                        null=False,
                                        related_name='updated_import_cases')
    variation_requests = models.ManyToManyField(VariationRequest)
    case_notes = models.ManyToManyField(CaseNote)
    further_information_requests = models.ManyToManyField(
        FurtherInformationRequest)
    update_requests = models.ManyToManyField(UpdateRequest)
    case_notes = models.ManyToManyField(CaseNote)


class ConstabularyEmail(models.Model):

    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    DRAFT = 'DRAFT'
    STATUSES = ((OPEN, 'Open'), (CLOSED, 'Closed'), (DRAFT, 'Draft'))

    is_active = models.BooleanField(blank=False, null=False, default=True)
    case = models.ForeignKey(ImportCase,
                             on_delete=models.PROTECT,
                             blank=False,
                             null=False)
    status = models.CharField(max_length=30,
                              blank=False,
                              null=False,
                              default=DRAFT)
    email_cc_address_list = models.CharField(max_length=4000,
                                             blank=True,
                                             null=True)
    email_subject = models.CharField(max_length=100, blank=False, null=True)
    email_body = models.TextField(max_length=4000, blank=False, null=True)
    email_response = models.TextField(max_length=4000, blank=True, null=True)
    email_sent_datetime = models.DateTimeField(blank=True, null=True)
    email_closed_datetime = models.DateTimeField(blank=True, null=True)
