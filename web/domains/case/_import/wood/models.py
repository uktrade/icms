from django.db import models

from ..models import ImportApplication


class WoodQuotaApplication(ImportApplication):
    PROCESS_TYPE = "WoodQuotaApplication"

    shipping_year = models.IntegerField(blank=False, null=True)

    exporter_name = models.CharField(max_length=100, blank=False, null=True)
    exporter_address = models.CharField(max_length=4000, blank=False, null=True)
    exporter_vat_nr = models.CharField(max_length=100, blank=False, null=True)

    # TODO: add the fields for the rest of the data:
    #  ICMSLST-559: goods
    #  ICMSLST-557: certificates/documents
    #  ICMSLST-558: supporting documents
