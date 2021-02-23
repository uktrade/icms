from django.db import models

from ..models import ImportApplication


class SanctionsAndAdhocApplication(ImportApplication):
    PROCESS_TYPE = "SanctionsAndAdhocApplication"

    exporter_name = models.CharField(max_length=4000, blank=True, null=True)
    exporter_address = models.CharField(max_length=4000, blank=True, null=True)
