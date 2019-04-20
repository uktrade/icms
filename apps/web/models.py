from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.query import QuerySet
from viewflow.models import Process


class User(AbstractUser):
    title = models.CharField(max_length=20, blank=False, null=True)
    phone = models.CharField(max_length=60, blank=False, null=True)
    organisation = models.CharField(max_length=4000, blank=False, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    security_question = models.CharField(
        max_length=4000, blank=False, null=True)
    security_answer = models.CharField(max_length=4000, blank=False, null=True)


class AccessRequestQuerySet(QuerySet):
    def importer_requests(self):
        return self.filter(request_type__in=[
            AccessRequest.IMPORTER, AccessRequest.IMPORTER_AGENT
        ])

    def exporter_requests(self):
        return self.filter(request_type__in=[
            AccessRequest.EXPORTER, AccessRequest.EXPORTER_AGENT
        ])


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


class AccessRequestProcess(Process):
    access_request = models.ForeignKey(AccessRequest, on_delete=models.CASCADE)
