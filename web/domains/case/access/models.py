import datetime

from django.db import models

from viewflow.models import Process
from web.domains.case.models import FurtherInformationRequest
from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.domains.user.models import User

from .managers import AccessRequestQuerySet, ProcessQuerySet


class AccessRequest(models.Model):

    # Request types
    IMPORTER = "MAIN_IMPORTER_ACCESS"
    IMPORTER_AGENT = "AGENT_IMPORTER_ACCESS"
    EXPORTER = "MAIN_EXPORTER_ACCESS"
    EXPORTER_AGENT = "AGENT_EXPORTER_ACCESS"

    REQUEST_TYPES = (
        (IMPORTER, 'Request access to act as an Importer'),
        (IMPORTER_AGENT, 'Request access to act as an Agent for an Importer'),
        (EXPORTER, 'Request access to act as an Exporter'),
        (EXPORTER_AGENT, 'Request access to act as an Agent for an Exporter'),
    )

    # Access Request status
    SUBMITTED = 'SUBMITTED'
    CLOSED = 'CLOSED'
    STATUSES = ((SUBMITTED, 'Submitted'), (CLOSED, 'Closed'))

    # Access Request response
    APPROVED = 'APPROVED'
    REFUSED = 'REFUSED'
    RESPONSES = ((APPROVED, 'Approved'), (REFUSED, 'Refused'))

    objects = AccessRequestQuerySet.as_manager()
    reference = models.CharField(max_length=50, blank=False, null=False)
    request_type = models.CharField(max_length=30,
                                    choices=REQUEST_TYPES,
                                    blank=False,
                                    null=False)
    status = models.CharField(max_length=30,
                              choices=STATUSES,
                              blank=False,
                              null=False,
                              default=SUBMITTED)
    organisation_name = models.CharField(max_length=100,
                                         blank=False,
                                         null=False)
    organisation_address = models.CharField(max_length=500,
                                            blank=False,
                                            null=True)
    request_reason = models.CharField(max_length=1000, blank=True, null=True)
    agent_name = models.CharField(max_length=100, blank=True, null=True)
    agent_address = models.CharField(max_length=500, blank=True, null=True)
    submit_datetime = models.DateTimeField(blank=False, null=False)
    submitted_by = models.ForeignKey(User,
                                     on_delete=models.PROTECT,
                                     blank=False,
                                     null=False,
                                     related_name='submitted_access_requests')
    last_update_datetime = models.DateTimeField(auto_now=True,
                                                blank=False,
                                                null=False)
    last_updated_by = models.ForeignKey(User,
                                        on_delete=models.PROTECT,
                                        blank=True,
                                        null=True,
                                        related_name='updated_access_requests')
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(User,
                                  on_delete=models.PROTECT,
                                  blank=True,
                                  null=True,
                                  related_name='closed_access_requests')
    response = models.CharField(max_length=20,
                                choices=RESPONSES,
                                blank=False,
                                null=True)
    response_reason = models.CharField(max_length=4000, blank=True, null=True)
    linked_importer = models.ForeignKey(Importer,
                                        on_delete=models.PROTECT,
                                        blank=True,
                                        null=True,
                                        related_name='access_requests')
    linked_exporter = models.ForeignKey(Exporter,
                                        on_delete=models.PROTECT,
                                        blank=True,
                                        null=True,
                                        related_name='access_requests')
    further_information_requests = models.ManyToManyField(
        FurtherInformationRequest)

    @property
    def request_type_verbose(self):
        return dict(AccessRequest.REQUEST_TYPES)[self.request_type]

    @property
    def request_type_short(self):
        if self.request_type in [self.IMPORTER, self.IMPORTER_AGENT]:
            return "Import Access Request"
        else:
            return "Exporter Access Request"

    @property
    def requester_type(self):
        if self.request_type in [self.IMPORTER, self.IMPORTER_AGENT]:
            return "importer"
        else:
            return "exporter"

    def save(self):
        # Set submit_datetime on save
        # audo_now=True causes field to be non-editable
        # and prevents from being added to a form
        self.submit_datetime = datetime.datetime.now()
        super().save()


class AccessRequestProcess(Process):
    access_request = models.ForeignKey(AccessRequest, on_delete=models.CASCADE)
    objects = ProcessQuerySet.as_manager()


class ApprovalRequest(models.Model):
    """
    Approval request for submitted requests.
    Approval requests are requested from importer/exporter
    contacts by case officers
    """

    # Approval Request response options
    APPROVE = 'APPROVE'
    REFUSE = 'REFUSE'
    RESPONSE_OPTIONS = ((APPROVE, 'Approve'), (REFUSE, 'Refuse'))

    # Approval Request status
    DRAFT = 'DRAFT'
    COMPLETED = 'COMPLETED'
    STATUSES = ((DRAFT, 'DRAFT'), (REFUSE, 'OPEN'))

    access_request = models.ForeignKey(AccessRequest,
                                       on_delete=models.CASCADE,
                                       blank=False,
                                       null=False)
    status = models.CharField(max_length=20,
                              choices=STATUSES,
                              blank=True,
                              null=True)
    request_date = models.DateTimeField(blank=True, null=True)
    requested_by = models.ForeignKey(User,
                                     on_delete=models.CASCADE,
                                     blank=True,
                                     null=True,
                                     related_name='approval_requests')
    requested_from = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='assigned_approval_requests')
    response = models.CharField(max_length=20,
                                choices=RESPONSE_OPTIONS,
                                blank=True,
                                null=True)
    response_by = models.ForeignKey(User,
                                    on_delete=models.CASCADE,
                                    blank=True,
                                    null=True,
                                    related_name='responded_approval_requests')
    response_date = models.DateTimeField(blank=True, null=True)
    response_reason = models.CharField(max_length=4000, blank=True, null=True)
