from django.db import models
from django.contrib.auth.models import AbstractUser
from viewflow.models import Process
from .managers import AccessRequestQuerySet, ProcessQuerySet


class User(AbstractUser):
    title = models.CharField(max_length=20, blank=False, null=True)
    phone = models.CharField(max_length=60, blank=False, null=True)
    organisation = models.CharField(max_length=4000, blank=False, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    security_question = models.CharField(
        max_length=4000, blank=False, null=True)
    security_answer = models.CharField(max_length=4000, blank=False, null=True)
    register_complete = models.BooleanField(
        blank=False, null=False, default=False)


class AccessRequest(models.Model):

    IMPORTER = "IMPORTER"
    IMPORTER_AGENT = "IMPORTER_AGENT"
    EXPORTER = "EXPORTER"
    EXPORTER_AGENT = "EXPORTER_AGENT"

    REQUEST_TYPES = (
        (IMPORTER, 'Request access to act as an Importer'),
        (IMPORTER_AGENT, 'Request access to act as an Agent for an Importer'),
        (EXPORTER, 'Request access to act as an Exporter'),
        (EXPORTER_AGENT, 'Request access to act as an Agent for an Exporter'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='access_requests')
    request_type = models.CharField(
        max_length=30, choices=REQUEST_TYPES, blank=False, null=False)
    organisation_name = models.CharField(
        max_length=100, blank=False, null=False)
    organisation_address = models.CharField(
        max_length=500, blank=False, null=False)
    description = models.CharField(max_length=1000, blank=False, null=False)
    agent_name = models.CharField(max_length=100, blank=False, null=False)
    agent_address = models.CharField(max_length=500, blank=False, null=False)
    objects = AccessRequestQuerySet.as_manager()

    def request_type_verbose(self):
        return dict(AccessRequest.REQUEST_TYPES)[self.request_type]

    def request_type_short(self):
        if self.request_type in [self.IMPORTER, self.IMPORTER_AGENT]:
            return "Import Access Request"
        else:
            return "Exporter Access Request"


class AccessRequestProcess(Process):
    access_request = models.ForeignKey(AccessRequest, on_delete=models.CASCADE)
    objects = ProcessQuerySet.as_manager()


class OutboundEmail(models.Model):
    FAILED = 'FAILED'
    SENT = 'SENT'
    PENDING = 'PENDING'
    NOT_SENT = 'NOT_SENT'

    STATUSES = (
        (FAILED, 'Failed'),
        (SENT, 'Sent'),
        (PENDING, 'Pending'),
        (NOT_SENT, 'Not Sent'),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUSES,
        blank=False,
        null=False,
        default=PENDING)
    last_requested_date = models.DateTimeField(
        auto_now_add=True, blank=False, null=False)
    format = models.CharField(
        max_length=20, blank=False, null=False, default='Email')
    to_name = models.CharField(max_length=170, null=True)
    to_email = models.CharField(max_length=254, null=False)
    subject = models.CharField(max_length=4000, null=True)


class EmailAttachment(models.Model):
    mail = models.ForeignKey(
        OutboundEmail, on_delete=models.CASCADE, related_name='attachments')
    filename = models.CharField(max_length=200, blank=True, null=True)
    mimetype = models.CharField(max_length=200, null=False)
    text_attachment = models.TextField(null=True)


class Template(models.Model):

    # Template types
    ENDORSEMENT = 'ENDORSEMENT'
    LETTER_TEMPLATE = 'LETTER_TEMPLATE'
    EMAIL_TEMPLATE = 'EMAIL_TEMPLATE'
    CFS_TRANSLATION = 'CFS_TRANSLATION'
    DECLARATION = 'DECLARATION'

    TYPES = (
        (ENDORSEMENT, 'Endorsement'),
        (LETTER_TEMPLATE, 'Letter template'),
        (EMAIL_TEMPLATE, 'Email template'),
        (CFS_TRANSLATION, 'CFS translation'),
        (DECLARATION, 'Declaration'),
    )

    # Application domain
    CERTIFICATE_APPLICATION = "CA"
    IMPORT_APPLICATION = "IMA"
    ACCESS_REQUEST = "IAR"

    DOMAINS = (
        (CERTIFICATE_APPLICATION, "Certificate Applications"),
        (IMPORT_APPLICATION, "Import Applications"),
        (ACCESS_REQUEST, "Access Requests"),
    )

    start_datetime = models.DateTimeField(blank=False, null=False)
    end_datetime = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(blank=False, null=False, default=False)
    template_name = models.CharField(max_length=100, blank=False, null=False)
    template_code = models.CharField(max_length=50, blank=True, null=True)
    template_type = models.CharField(
        max_length=20, choices=TYPES, blank=False, null=False)
    application_domain = models.CharField(
        max_length=20, choices=DOMAINS, blank=False, null=False)

    def template_type_verbose(self):
        return dict(Template.TYPES)[self.template_type]

    def application_domain_verbose(self):
        return dict(Template.DOMAINS)[self.application_domain]
