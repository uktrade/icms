import structlog as logging
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone
from viewflow.models import Process

from web.domains.case.fir.mixins import FurtherInformationProcessMixin
from web.domains.case.fir.models import FurtherInformationRequest, FurtherInformationRequestProcess
from web.domains.exporter.models import Exporter
from web.domains.importer.models import Importer
from web.domains.template.models import Template
from web.domains.user.models import User

from .managers import AccessRequestQuerySet

logger = logging.getLogger(__name__)


def _get_fir_template():
    """Fetch template for initial FIR request details"""
    return Template.objects.get(template_code="IAR_RFI_EMAIL", is_active=True)


def _render_template_content(request, template, access_request):
    return template.get_content(
        {
            "CURRENT_USER_NAME": request.user.full_name,
            "REQUESTER_NAME": access_request.submitted_by.full_name,
        }
    )


def _render_template_title(template, access_request):
    # TODO: Use reference here, currently using access_id as reference is not generated
    return template.get_title({"REQUEST_REFERENCE": access_request.id})


class AccessRequest(models.Model):

    # Request types
    IMPORTER = "MAIN_IMPORTER_ACCESS"
    IMPORTER_DESC = "Request access to act as an Importer"
    IMPORTER_AGENT = "AGENT_IMPORTER_ACCESS"
    IMPORTER_AGENT_DESC = "Request access to act as an Agent for an Importer"
    EXPORTER = "MAIN_EXPORTER_ACCESS"
    EXPORTER_DESC = "Request access to act as an Exporter"
    EXPORTER_AGENT = "AGENT_EXPORTER_ACCESS"
    EXPORTER_AGENT_DESC = "Request access to act as an Agent for an Exporter"

    REQUEST_TYPES = (
        (IMPORTER, IMPORTER_DESC),
        (IMPORTER_AGENT, IMPORTER_AGENT_DESC),
        (EXPORTER, EXPORTER_DESC),
        (EXPORTER_AGENT, EXPORTER_AGENT_DESC),
    )
    IMPORTER_REQUEST_TYPES = ((IMPORTER, IMPORTER_DESC), (IMPORTER_AGENT, IMPORTER_AGENT_DESC))
    EXPORTER_REQUEST_TYPES = ((EXPORTER, EXPORTER_DESC), (EXPORTER_AGENT, EXPORTER_AGENT_DESC))

    # Access Request status
    SUBMITTED = "SUBMITTED"
    CLOSED = "CLOSED"
    STATUSES = ((SUBMITTED, "Submitted"), (CLOSED, "Closed"))

    # Access Request response
    APPROVED = "APPROVED"
    REFUSED = "REFUSED"
    RESPONSES = ((APPROVED, "Approved"), (REFUSED, "Refused"))

    objects = AccessRequestQuerySet.as_manager()
    reference = models.CharField(max_length=50, blank=False, null=False)
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPES, blank=False, null=False)
    status = models.CharField(
        max_length=30, choices=STATUSES, blank=False, null=False, default=SUBMITTED
    )
    organisation_name = models.CharField(max_length=100, blank=False, null=False)
    organisation_address = models.CharField(max_length=500, blank=False, null=True)
    request_reason = models.CharField(max_length=1000, blank=True, null=True)
    agent_name = models.CharField(max_length=100, blank=True, null=True)
    agent_address = models.CharField(max_length=500, blank=True, null=True)
    submit_datetime = models.DateTimeField(blank=False, null=False)
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=False,
        null=False,
        related_name="submitted_access_requests",
    )
    last_update_datetime = models.DateTimeField(auto_now=True, blank=False, null=False)
    last_updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="updated_access_requests",
    )
    closed_datetime = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, blank=True, null=True, related_name="closed_access_requests"
    )
    response = models.CharField(max_length=20, choices=RESPONSES, blank=False, null=True)
    response_reason = models.CharField(max_length=4000, blank=True, null=True)
    linked_importer = models.ForeignKey(
        Importer, on_delete=models.PROTECT, blank=True, null=True, related_name="access_requests"
    )
    linked_exporter = models.ForeignKey(
        Exporter, on_delete=models.PROTECT, blank=True, null=True, related_name="access_requests"
    )
    further_information_requests = models.ManyToManyField(FurtherInformationRequest)

    @property
    def request_type_verbose(self):
        return dict(AccessRequest.REQUEST_TYPES)[self.request_type]

    @property
    def request_type_short(self):
        if self.request_type in [self.IMPORTER, self.IMPORTER_AGENT]:
            return "Importer Access Request"
        else:
            return "Exporter Access Request"

    @property
    def requester_type(self):
        if self.is_importer_request():
            return "importer"
        else:
            return "exporter"

    def is_importer_request(self):
        return self.request_type in [self.IMPORTER, self.IMPORTER_AGENT]

    def is_exporter_request(self):
        return self.request_type in [self.EXPORTER, self.EXPORTER_AGENT]

    def is_agent_request(self):
        return self.request_type in [self.IMPORTER_AGENT, self.EXPORTER_AGENT]

    def save(self, *args, **kwargs):
        # Set submit_datetime on save
        # audo_now=True causes field to be non-editable
        # and prevents from being added to a form
        self.submit_datetime = timezone.now()
        super().save(*args, **kwargs)


class ImporterAccessRequestProcess(FurtherInformationProcessMixin, Process):

    IMP_CASE_OFFICER = "web.IMP_CASE_OFFICER"  # case officer permission
    IMP_AGENT_APPROVER = "web.IMP_AGENT_APPROVER"  # importer permission for fir response
    FIR_TEMPLATE_CODE = "IAR_RFI_EMAIL"

    access_request = models.ForeignKey(AccessRequest, null=True, on_delete=models.SET_NULL)
    approval_required = models.BooleanField(blank=False, null=False, default=False)

    restart_approval = models.BooleanField(blank=False, null=False, default=False)
    re_link = models.BooleanField(blank=False, null=False, default=False)
    fir_processes = GenericRelation(FurtherInformationRequestProcess)

    def fir_content(self, request):
        template = _get_fir_template()
        return {
            "request_subject": _render_template_title(template, self.access_request),
            "request_detail": _render_template_content(request, template, self.access_request),
        }

    def fir_config(self):
        return {
            "requester_permission": self.IMP_CASE_OFFICER,
            "responder_permission": self.IMP_AGENT_APPROVER,
            "responder_team": self.access_request.linked_importer,
            "namespace": "access:importer",
        }

    def on_fir_create(self, fir):
        self.access_request.further_information_requests.add(fir)


class ExporterAccessRequestProcess(FurtherInformationProcessMixin, Process):
    # Importer and exporter access request flows can't share
    # the same model as view permissions for access and importer case officers
    # are separate

    IMP_CERT_CASE_OFFICER = "web.IMP_CERT_CASE_OFFICER"  # case officer permission
    IMP_CERT_AGENT_APPROVER = "web.IMP_CERT_AGENT_APPROVER"  # exporter permission for fir response
    FIR_TEMPLATE_CODE = "IAR_RFI_EMAIL"

    access_request = models.ForeignKey(AccessRequest, null=True, on_delete=models.SET_NULL)
    approval_required = models.BooleanField(blank=False, null=False, default=False)

    restart_approval = models.BooleanField(blank=False, null=False, default=False)
    re_link = models.BooleanField(blank=False, null=False, default=False)
    fir_processes = GenericRelation(FurtherInformationRequestProcess)

    def fir_content(self, request):
        template = _get_fir_template()
        return {
            "request_subject": _render_template_title(template, self.access_request),
            "request_detail": _render_template_content(request, template, self.access_request),
        }

    def fir_config(self):
        return {
            "requester_permission": self.IMP_CERT_CASE_OFFICER,
            "responder_permission": self.IMP_CERT_AGENT_APPROVER,
            "responder_team": self.access_request.linked_exporter,
            "namespace": "access:exporter",
        }

    def on_fir_create(self, fir):
        self.access_request.further_information_requests.add(fir)
